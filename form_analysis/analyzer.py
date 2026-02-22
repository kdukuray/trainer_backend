"""
YOLO-based form analysis engine for 5 exercises.

Ported from the Streamlit prototype in ``formTracking/unified_form_tracker.py``
and extended to support bench press, curls, and crunches. Each exercise has its
own state machine and metric evaluation logic.

This module is Streamlit-free — it takes a video file path and returns a
structured result dict.
"""

import logging
import tempfile

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Process every Nth frame to balance speed and accuracy
FRAME_STRIDE = 3

# ──────────────────────────── Geometry helpers ────────────────────────────


def calculate_angle(point_a, point_b, point_c) -> float:
    """
    Calculate the angle (degrees) at vertex *point_b* formed by *point_a*
    and *point_c* using the cosine rule.
    """
    a = np.array(point_a)
    b = np.array(point_b)
    c = np.array(point_c)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba == 0 or norm_bc == 0:
        return 0.0

    cosine = np.clip(np.dot(ba, bc) / (norm_ba * norm_bc), -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


# ──────────────────────────── Keypoint extraction ────────────────────────


def _get_keypoint(person_kpts, idx):
    """Return a keypoint array or None if it is missing / zero."""
    if idx < len(person_kpts) and person_kpts[idx][0] != 0 and person_kpts[idx][1] != 0:
        return person_kpts[idx]
    return None


def _extract_main_person(results):
    """
    From YOLO results pick the highest-confidence person and return their
    COCO keypoints array, or None if nothing was detected.
    """
    if results is None or len(results) == 0:
        return None
    r = results[0]
    if r.keypoints is None or r.keypoints.xy is None:
        return None
    kpts = r.keypoints.xy
    if kpts.shape[0] == 0:
        return None
    dets = r.boxes
    if dets is None or len(dets) == 0:
        return None
    scores = dets.conf.cpu().numpy()
    main_idx = int(scores.argmax())
    return kpts[main_idx].cpu().numpy()


# COCO-17 keypoint indices
NOSE = 0
L_SHOULDER, R_SHOULDER = 5, 6
L_ELBOW, R_ELBOW = 7, 8
L_WRIST, R_WRIST = 9, 10
L_HIP, R_HIP = 11, 12
L_KNEE, R_KNEE = 13, 14

# ──────────────────────────── Exercise analyzers ─────────────────────────


def _analyze_pushups(video_path: str) -> dict:
    """
    Analyse push-up form using elbow flare angle.

    Metric: Angle at the shoulder vertex formed by hip-shoulder-elbow.
    Good rep: median angle during the down phase <= 75 deg.
    """
    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(video_path)

    state = "up"
    min_y = max_y = None
    current_rep_angles: list[float] = []
    rep_details: list[dict] = []
    good = bad = 0
    threshold = 75.0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % FRAME_STRIDE != 0:
            continue

        person = _extract_main_person(model(frame, verbose=False))
        if person is None:
            continue

        kpts = {
            "l_sh": _get_keypoint(person, L_SHOULDER),
            "r_sh": _get_keypoint(person, R_SHOULDER),
            "l_el": _get_keypoint(person, L_ELBOW),
            "r_el": _get_keypoint(person, R_ELBOW),
            "l_hip": _get_keypoint(person, L_HIP),
            "r_hip": _get_keypoint(person, R_HIP),
        }

        y_coords = [k[1] for k in kpts.values() if k is not None]
        if not y_coords:
            continue
        torso_y = float(np.mean(y_coords))

        if min_y is None:
            min_y = max_y = torso_y
        min_y = min(min_y, torso_y)
        max_y = max(max_y, torso_y)

        span = max_y - min_y
        down_thresh = min_y + 0.6 * span if span > 0 else min_y
        up_thresh = min_y + 0.3 * span if span > 0 else max_y

        # Angle calculation
        angles = []
        if kpts["l_sh"] is not None and kpts["l_hip"] is not None and kpts["l_el"] is not None:
            angles.append(calculate_angle(kpts["l_hip"], kpts["l_sh"], kpts["l_el"]))
        if kpts["r_sh"] is not None and kpts["r_hip"] is not None and kpts["r_el"] is not None:
            angles.append(calculate_angle(kpts["r_hip"], kpts["r_sh"], kpts["r_el"]))
        valid = [a for a in angles if a > 10]
        flare = float(np.mean(valid)) if valid else 0

        if state == "up" and torso_y > down_thresh:
            state = "down"
            current_rep_angles = []
        if state == "down":
            if flare > 0:
                current_rep_angles.append(flare)
            if torso_y < up_thresh:
                state = "up"
                if current_rep_angles:
                    median_flare = float(np.median(current_rep_angles))
                    rep_num = good + bad + 1
                    if median_flare > threshold:
                        bad += 1
                        rep_details.append({
                            "rep": rep_num,
                            "status": "bad",
                            "metric_value": round(median_flare, 1),
                            "feedback": f"Elbow flare too wide ({round(median_flare, 1)}° > {threshold}°). Keep elbows closer to your body.",
                        })
                    else:
                        good += 1
                        rep_details.append({
                            "rep": rep_num,
                            "status": "good",
                            "metric_value": round(median_flare, 1),
                            "feedback": "Good form — elbows tucked properly.",
                        })

    cap.release()
    return {"total_reps": good + bad, "good_reps": good, "bad_reps": bad, "rep_details": rep_details}


def _analyze_pullups(video_path: str) -> dict:
    """
    Analyse pull-up form using chin-above-bar criterion.

    Good rep: Nose Y goes above average shoulder Y at some point during the up phase.
    """
    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(video_path)

    state = "down"
    min_head_y = max_head_y = None
    chin_above_bar = False
    rep_details: list[dict] = []
    good = bad = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % FRAME_STRIDE != 0:
            continue

        person = _extract_main_person(model(frame, verbose=False))
        if person is None:
            continue

        nose = _get_keypoint(person, NOSE)
        l_sh = _get_keypoint(person, L_SHOULDER)
        r_sh = _get_keypoint(person, R_SHOULDER)

        if nose is None:
            continue
        head_y = float(nose[1])

        sh_ys = []
        if l_sh is not None:
            sh_ys.append(l_sh[1])
        if r_sh is not None:
            sh_ys.append(r_sh[1])
        shoulder_y = float(np.mean(sh_ys)) if sh_ys else None

        if min_head_y is None:
            min_head_y = max_head_y = head_y
        min_head_y = min(min_head_y, head_y)
        max_head_y = max(max_head_y, head_y)

        head_range = max_head_y - min_head_y
        top_thresh = min_head_y + 0.3 * head_range if head_range > 0 else min_head_y
        bottom_thresh = min_head_y + 0.7 * head_range if head_range > 0 else max_head_y

        if state == "down" and head_y < top_thresh:
            state = "up"
            chin_above_bar = False
        if state == "up":
            if shoulder_y is not None and head_y < shoulder_y:
                chin_above_bar = True
            if head_y > bottom_thresh:
                state = "down"
                rep_num = good + bad + 1
                if chin_above_bar:
                    good += 1
                    rep_details.append({"rep": rep_num, "status": "good", "metric_value": 1, "feedback": "Chin cleared the bar — full range of motion."})
                else:
                    bad += 1
                    rep_details.append({"rep": rep_num, "status": "bad", "metric_value": 0, "feedback": "Chin did not clear bar height. Pull higher."})

    cap.release()
    return {"total_reps": good + bad, "good_reps": good, "bad_reps": bad, "rep_details": rep_details}


def _analyze_bench_press(video_path: str) -> dict:
    """
    Analyse bench press form from a side view.

    Metrics:
    - Elbow angle at bottom of press (~80-100 deg is good).
    - Lockout at top (elbow angle > 160 deg).
    """
    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(video_path)

    state = "up"
    min_wrist_y = max_wrist_y = None
    current_rep_bottom_angles: list[float] = []
    lockout_reached = False
    rep_details: list[dict] = []
    good = bad = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % FRAME_STRIDE != 0:
            continue

        person = _extract_main_person(model(frame, verbose=False))
        if person is None:
            continue

        # Use the most visible side
        l_sh = _get_keypoint(person, L_SHOULDER)
        r_sh = _get_keypoint(person, R_SHOULDER)
        l_el = _get_keypoint(person, L_ELBOW)
        r_el = _get_keypoint(person, R_ELBOW)
        l_wr = _get_keypoint(person, L_WRIST)
        r_wr = _get_keypoint(person, R_WRIST)

        # Pick the side with more visible keypoints
        left_ok = all(k is not None for k in [l_sh, l_el, l_wr])
        right_ok = all(k is not None for k in [r_sh, r_el, r_wr])

        if not left_ok and not right_ok:
            continue

        if left_ok:
            elbow_angle_l = calculate_angle(l_sh, l_el, l_wr)
            wrist_y_l = float(l_wr[1])
        else:
            elbow_angle_l = None
            wrist_y_l = None

        if right_ok:
            elbow_angle_r = calculate_angle(r_sh, r_el, r_wr)
            wrist_y_r = float(r_wr[1])
        else:
            elbow_angle_r = None
            wrist_y_r = None

        # Use the visible side's values
        valid_angles = [a for a in [elbow_angle_l, elbow_angle_r] if a is not None]
        valid_wrists = [w for w in [wrist_y_l, wrist_y_r] if w is not None]
        if not valid_angles or not valid_wrists:
            continue

        elbow_angle = float(np.mean(valid_angles))
        wrist_y = float(np.mean(valid_wrists))

        if min_wrist_y is None:
            min_wrist_y = max_wrist_y = wrist_y
        min_wrist_y = min(min_wrist_y, wrist_y)
        max_wrist_y = max(max_wrist_y, wrist_y)

        span = max_wrist_y - min_wrist_y
        down_thresh = min_wrist_y + 0.6 * span if span > 0 else min_wrist_y
        up_thresh = min_wrist_y + 0.3 * span if span > 0 else max_wrist_y

        # State machine: track wrist position (higher Y = closer to chest = down)
        if state == "up" and wrist_y > down_thresh:
            state = "down"
            current_rep_bottom_angles = []
            lockout_reached = False
        if state == "down":
            current_rep_bottom_angles.append(elbow_angle)
            if wrist_y < up_thresh:
                state = "up"
                lockout_reached = elbow_angle > 160

                rep_num = good + bad + 1
                min_angle = float(np.min(current_rep_bottom_angles)) if current_rep_bottom_angles else 0
                issues: list[str] = []

                if min_angle < 70:
                    issues.append(f"Went too deep ({round(min_angle, 1)}°). Aim for 80-100° at bottom.")
                elif min_angle > 110:
                    issues.append(f"Insufficient depth ({round(min_angle, 1)}°). Lower the bar more.")
                if not lockout_reached:
                    issues.append("Did not fully lock out at the top.")

                if issues:
                    bad += 1
                    rep_details.append({"rep": rep_num, "status": "bad", "metric_value": round(min_angle, 1), "feedback": " ".join(issues)})
                else:
                    good += 1
                    rep_details.append({"rep": rep_num, "status": "good", "metric_value": round(min_angle, 1), "feedback": "Good depth and full lockout."})

    cap.release()
    return {"total_reps": good + bad, "good_reps": good, "bad_reps": bad, "rep_details": rep_details}


def _analyze_curls(video_path: str) -> dict:
    """
    Analyse bicep curl form from a side view.

    Metrics:
    - Full range of motion: elbow angle should go from ~160 deg (extended) to ~30 deg (contracted).
    - Upper arm stability: shoulder-elbow segment angle change should be minimal.
    """
    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(video_path)

    state = "down"
    min_angle = max_angle = None
    current_rep_angles: list[float] = []
    upper_arm_angles: list[float] = []
    rep_details: list[dict] = []
    good = bad = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % FRAME_STRIDE != 0:
            continue

        person = _extract_main_person(model(frame, verbose=False))
        if person is None:
            continue

        l_sh = _get_keypoint(person, L_SHOULDER)
        r_sh = _get_keypoint(person, R_SHOULDER)
        l_el = _get_keypoint(person, L_ELBOW)
        r_el = _get_keypoint(person, R_ELBOW)
        l_wr = _get_keypoint(person, L_WRIST)
        r_wr = _get_keypoint(person, R_WRIST)
        l_hip = _get_keypoint(person, L_HIP)
        r_hip = _get_keypoint(person, R_HIP)

        left_ok = all(k is not None for k in [l_sh, l_el, l_wr])
        right_ok = all(k is not None for k in [r_sh, r_el, r_wr])

        if not left_ok and not right_ok:
            continue

        angles = []
        ua_angles = []
        if left_ok:
            angles.append(calculate_angle(l_sh, l_el, l_wr))
            if l_hip is not None:
                ua_angles.append(calculate_angle(l_hip, l_sh, l_el))
        if right_ok:
            angles.append(calculate_angle(r_sh, r_el, r_wr))
            if r_hip is not None:
                ua_angles.append(calculate_angle(r_hip, r_sh, r_el))

        elbow_angle = float(np.mean(angles))
        ua_angle = float(np.mean(ua_angles)) if ua_angles else None

        if min_angle is None:
            min_angle = max_angle = elbow_angle
        min_angle = min(min_angle, elbow_angle)
        max_angle = max(max_angle, elbow_angle)

        angle_range = max_angle - min_angle
        curl_thresh = min_angle + 0.35 * angle_range if angle_range > 0 else min_angle
        extend_thresh = min_angle + 0.65 * angle_range if angle_range > 0 else max_angle

        if state == "down" and elbow_angle < curl_thresh:
            state = "up"
            current_rep_angles = []
            upper_arm_angles = []
        if state == "up":
            current_rep_angles.append(elbow_angle)
            if ua_angle is not None:
                upper_arm_angles.append(ua_angle)
            if elbow_angle > extend_thresh:
                state = "down"
                rep_num = good + bad + 1
                issues: list[str] = []

                rep_min = float(np.min(current_rep_angles)) if current_rep_angles else 90
                rep_max = float(np.max(current_rep_angles)) if current_rep_angles else 90
                rom = rep_max - rep_min

                if rom < 80:
                    issues.append(f"Limited range of motion ({round(rom, 1)}°). Extend fully and curl completely.")

                if upper_arm_angles and (float(np.std(upper_arm_angles)) > 12):
                    issues.append("Upper arm is swinging. Keep your elbow pinned to your side.")

                if issues:
                    bad += 1
                    rep_details.append({"rep": rep_num, "status": "bad", "metric_value": round(rom, 1), "feedback": " ".join(issues)})
                else:
                    good += 1
                    rep_details.append({"rep": rep_num, "status": "good", "metric_value": round(rom, 1), "feedback": "Good range of motion and stable upper arm."})

    cap.release()
    return {"total_reps": good + bad, "good_reps": good, "bad_reps": bad, "rep_details": rep_details}


def _analyze_crunches(video_path: str) -> dict:
    """
    Analyse crunch form from a side view.

    Metrics:
    - Shoulder lift angle relative to ground (30-45 deg is ideal).
    - Neck position: nose should stay roughly aligned with shoulder (no neck cranking).
    """
    from ultralytics import YOLO

    model = YOLO("yolov8n-pose.pt")
    cap = cv2.VideoCapture(video_path)

    state = "down"
    min_shoulder_y = max_shoulder_y = None
    current_rep_lifts: list[float] = []
    rep_details: list[dict] = []
    good = bad = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % FRAME_STRIDE != 0:
            continue

        person = _extract_main_person(model(frame, verbose=False))
        if person is None:
            continue

        nose = _get_keypoint(person, NOSE)
        l_sh = _get_keypoint(person, L_SHOULDER)
        r_sh = _get_keypoint(person, R_SHOULDER)
        l_hip = _get_keypoint(person, L_HIP)
        r_hip = _get_keypoint(person, R_HIP)

        sh_pts = [p for p in [l_sh, r_sh] if p is not None]
        hip_pts = [p for p in [l_hip, r_hip] if p is not None]
        if not sh_pts or not hip_pts:
            continue

        shoulder_y = float(np.mean([p[1] for p in sh_pts]))
        hip_y = float(np.mean([p[1] for p in hip_pts]))
        shoulder_x = float(np.mean([p[0] for p in sh_pts]))
        hip_x = float(np.mean([p[0] for p in hip_pts]))

        # Compute trunk angle from horizontal
        dx = abs(shoulder_x - hip_x)
        dy = hip_y - shoulder_y  # positive means shoulder is higher (lower Y)
        trunk_angle = float(np.degrees(np.arctan2(dy, dx))) if dx > 0 else 0

        if min_shoulder_y is None:
            min_shoulder_y = max_shoulder_y = shoulder_y
        min_shoulder_y = min(min_shoulder_y, shoulder_y)
        max_shoulder_y = max(max_shoulder_y, shoulder_y)

        span = max_shoulder_y - min_shoulder_y
        up_thresh = min_shoulder_y + 0.35 * span if span > 0 else min_shoulder_y
        down_thresh = min_shoulder_y + 0.65 * span if span > 0 else max_shoulder_y

        if state == "down" and shoulder_y < up_thresh:
            state = "up"
            current_rep_lifts = []
        if state == "up":
            current_rep_lifts.append(trunk_angle)
            if shoulder_y > down_thresh:
                state = "down"
                rep_num = good + bad + 1
                max_lift = float(np.max(current_rep_lifts)) if current_rep_lifts else 0
                issues: list[str] = []

                if max_lift < 20:
                    issues.append(f"Insufficient lift ({round(max_lift, 1)}°). Curl your torso up more.")
                elif max_lift > 55:
                    issues.append(f"Over-flexion ({round(max_lift, 1)}°). You're doing a sit-up, not a crunch.")

                # Check neck cranking using nose position relative to shoulders
                if nose is not None and sh_pts:
                    nose_sh_dist = abs(float(nose[1]) - shoulder_y)
                    if nose_sh_dist > 60:
                        issues.append("Neck appears strained. Keep your gaze upward and don't pull your head forward.")

                if issues:
                    bad += 1
                    rep_details.append({"rep": rep_num, "status": "bad", "metric_value": round(max_lift, 1), "feedback": " ".join(issues)})
                else:
                    good += 1
                    rep_details.append({"rep": rep_num, "status": "good", "metric_value": round(max_lift, 1), "feedback": "Good crunch form — proper lift and neutral neck."})

    cap.release()
    return {"total_reps": good + bad, "good_reps": good, "bad_reps": bad, "rep_details": rep_details}


# ──────────────────────────── Public API ─────────────────────────────────

# Maps exercise name (lowercase) to its analyzer function
ANALYZERS = {
    "push-ups": _analyze_pushups,
    "pull-ups": _analyze_pullups,
    "bench press": _analyze_bench_press,
    "curls": _analyze_curls,
    "crunches": _analyze_crunches,
}


def analyze_video(exercise_name: str, video_path: str) -> dict:
    """
    Run form analysis on a video for the given exercise.

    Parameters:
        exercise_name: One of the 5 supported exercise names (case-insensitive).
        video_path: Path to the video file on disk.

    Returns:
        Dict with total_reps, good_reps, bad_reps, rep_details.

    Raises:
        ValueError: If the exercise is not supported.
    """
    analyzer = ANALYZERS.get(exercise_name.lower())
    if analyzer is None:
        raise ValueError(
            f"Unsupported exercise '{exercise_name}'. "
            f"Supported: {list(ANALYZERS.keys())}"
        )
    return analyzer(video_path)


def generate_load_suggestion(exercise_name: str, good_reps: int, total_reps: int) -> str:
    """
    Generate a plain-text suggestion for load adjustment based on form quality.

    Parameters:
        exercise_name: The exercise that was analyzed.
        good_reps: Number of reps with good form.
        total_reps: Total number of reps detected.

    Returns:
        A short coaching suggestion string.
    """
    if total_reps == 0:
        return "No reps detected. Try recording from the recommended angle with better lighting."

    ratio = good_reps / total_reps

    if ratio == 1.0:
        return (
            f"Excellent form on all {total_reps} reps! "
            "Consider increasing weight or reps for progressive overload."
        )
    elif ratio >= 0.75:
        return (
            f"Good form on {good_reps}/{total_reps} reps. "
            "Maintain current load and focus on perfecting the remaining reps."
        )
    elif ratio >= 0.5:
        return (
            f"Form broke down on {total_reps - good_reps} reps. "
            "Consider reducing weight by 5-10% to build better movement patterns."
        )
    else:
        return (
            f"Only {good_reps}/{total_reps} reps had good form. "
            "Reduce the load significantly and focus on controlled, quality reps."
        )
