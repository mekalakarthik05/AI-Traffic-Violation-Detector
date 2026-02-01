import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image
import glob

st.set_page_config(page_title="Traffic Violation Dashboard", layout="wide")

st.title("🚦 AI Traffic Violation Detector Dashboard")

# ================= LOAD EVIDENCE =================
def load_evidence():
    evidence_list = []
    images_dir = "evidence/images/"

    if not os.path.exists(images_dir):
        return evidence_list

    image_files = glob.glob(os.path.join(images_dir, "*.jpg"))

    for image_path in image_files:
        filename = os.path.basename(image_path)
        parts = filename.replace(".jpg", "").split("_")

        # Expected: violation_vehicleid_YYYYMMDD_HHMMSS.jpg
        if len(parts) >= 4:
            violation_type = "_".join(parts[:-3])
            vehicle_id = parts[-3]
            timestamp_str = f"{parts[-2]}_{parts[-1]}"

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except ValueError:
                timestamp = datetime.now()

            evidence_list.append({
                "violation_type": violation_type,
                "timestamp": timestamp,
                "image_path": image_path,
                "license_plate": f"LP-{vehicle_id}",
                "vehicle_id": vehicle_id
            })

    return sorted(evidence_list, key=lambda x: x["timestamp"], reverse=True)


violations = load_evidence()

# ================= SIDEBAR =================
st.sidebar.header("Filters")

violation_types = ["All"] + sorted(set(v["violation_type"] for v in violations))
selected_violation = st.sidebar.selectbox("Violation Type", violation_types)

time_range = st.sidebar.selectbox(
    "Time Range",
    ["Last Hour", "Last 24 Hours", "Last Week", "All Time"]
)

filtered_violations = violations

if selected_violation != "All":
    filtered_violations = [
        v for v in filtered_violations
        if v["violation_type"] == selected_violation
    ]

now = datetime.now()
if time_range == "Last Hour":
    cutoff = now - timedelta(hours=1)
elif time_range == "Last 24 Hours":
    cutoff = now - timedelta(days=1)
elif time_range == "Last Week":
    cutoff = now - timedelta(weeks=1)
else:
    cutoff = datetime.min

filtered_violations = [
    v for v in filtered_violations if v["timestamp"] >= cutoff
]

# ================= LAYOUT =================
left_col, right_col = st.columns([2, 1])

# ================= LEFT COLUMN =================
with left_col:
    st.subheader("Recent Violations")

    if filtered_violations:
        for idx, violation in enumerate(filtered_violations[:20]):

            with st.expander(
                f"{violation['violation_type'].replace('_', ' ').title()} "
                f"- {violation['timestamp'].strftime('%H:%M:%S %d/%m/%Y')}"
            ):
                img_col, info_col = st.columns([1.1, 2])

                # ---- IMAGE PREVIEW ----
                with img_col:
                    try:
                        img = Image.open(violation["image_path"])
                        st.image(img, width=320)
                    except Exception as e:
                        st.error(f"Image load error: {e}")

                # ---- DETAILS + ACTIONS ----
                with info_col:
                    st.markdown(
                        f"""
                        **Type:** {violation['violation_type'].replace('_', ' ').title()}  
                        **Time:** {violation['timestamp'].strftime('%H:%M:%S %d/%m/%Y')}  
                        **License Plate:** {violation['license_plate']}  
                        **Vehicle ID:** {violation['vehicle_id']}
                        """
                    )

                    st.markdown("---")

                    # Placeholder for inline full image
                    full_image_container = st.container()

                    btn1, btn2 = st.columns(2)

                    with btn1:
                        if st.button("🔍 View Full Image", key=f"view_{idx}"):
                            with full_image_container:
                                st.markdown("### 📸 Full Evidence Image")
                                try:
                                    full_img = Image.open(violation["image_path"])
                                    st.image(full_img, use_container_width=True)
                                except Exception as e:
                                    st.error(f"Could not load full image: {e}")

                    with btn2:
                        st.download_button(
                            label="⬇️ Download Evidence",
                            data=open(violation["image_path"], "rb"),
                            file_name=os.path.basename(violation["image_path"]),
                            mime="image/jpeg",
                            key=f"download_{idx}"
                        )
    else:
        st.info("No violations detected in the selected time range.")

# ================= RIGHT COLUMN =================
with right_col:
    st.subheader("Statistics")

    st.metric("Total Violations", len(filtered_violations))

    st.subheader("Violation Types")
    type_counts = {}
    for v in filtered_violations:
        type_counts[v["violation_type"]] = type_counts.get(v["violation_type"], 0) + 1

    for vt, count in type_counts.items():
        st.metric(vt.replace("_", " ").title(), count)

    if filtered_violations:
        st.subheader("Violations Over Time")

        hourly_counts = {}
        for v in filtered_violations:
            hour = v["timestamp"].strftime("%Y-%m-%d %H:00")
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

        hours, counts = zip(*sorted(hourly_counts.items()))
        chart_data = pd.DataFrame({"Violations": counts}, index=hours)
        st.line_chart(chart_data)

# ================= FOOTER =================
st.markdown("---")
st.markdown("**AI Traffic Violation Detector** – Real-time monitoring for safer roads")

# ================= EXPORT =================
if st.sidebar.button("Export Report"):
    if filtered_violations:
        df = pd.DataFrame([{
            "Violation Type": v["violation_type"],
            "Timestamp": v["timestamp"],
            "License Plate": v["license_plate"],
            "Vehicle ID": v["vehicle_id"],
            "Image Path": v["image_path"]
        } for v in filtered_violations])

        st.sidebar.download_button(
            "Download CSV Report",
            df.to_csv(index=False),
            "violation_report.csv",
            "text/csv"
        )
    else:
        st.sidebar.warning("No violations to export.")
