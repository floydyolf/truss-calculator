import streamlit as st
import pandas as pd

def find_truss_combinations(target, lengths, max_tolerance=100):
    """
    Finds combinations of truss pieces to hit a target length (in mm),
    filtered strictly for structural integrity and minimum piece count.
    """
    valid_results = []
    lengths = sorted(lengths, reverse=True) # Prioritize large pieces
    
    def backtrack(remain, current_combo, start_index, current_target):
        if remain == 0:
            # Structural Integrity check: Max 4 pieces smaller than 1000mm (1m)
            small_pieces_count = sum(1 for x in current_combo if x < 1000)
            if small_pieces_count <= 4:
                valid_results.append((current_target, list(current_combo)))
            return
        if remain < 0:
            return
            
        for i in range(start_index, len(lengths)):
            piece = lengths[i]
            if piece > remain:
                continue
            current_combo.append(piece)
            backtrack(remain - piece, current_combo, i, current_target)
            current_combo.pop()

    # Search across the allowable tolerance spectrum (in mm)
    for exact_target in range(target - max_tolerance, target + max_tolerance + 1):
        backtrack(exact_target, [], 0, exact_target)
        
    return valid_results

# --- STREAMLIT UI ---
st.set_page_config(page_title="Truss Calculator", page_icon="🏗️", layout="centered")

st.title("🏗️ Truss Combo")
st.write("Select your truss type, available stock and get a combo.")

# --- SIDEBAR: TRUSS INVENTORY CONFIGURATION ---
st.sidebar.header("📦 Inventory Management")

# Preset Profiles
truss_profiles = {
    "H30D": [250, 290, 500, 645, 710, 1000, 2000, 3000],
    "H30V": [250, 290, 440, 500, 560, 630, 710, 1000, 2000, 3000]
}

selected_profile = st.sidebar.selectbox("Select Truss Type:", list(truss_profiles.keys()))

# Get standard lengths for the selected profile
standard_lengths = truss_profiles[selected_profile]

st.sidebar.subheader("Active Stock")
st.sidebar.write("Uncheck lengths that are unavailable:")

# Build a dynamic list of lengths based on user checkboxes
available_lengths = []
for length in standard_lengths:
    if st.sidebar.checkbox(f"{length} mm", value=True, key=f"len_{length}"):
        available_lengths.append(length)


# --- MAIN INTERFACE ---
col1, col2 = st.columns(2)
with col1:
    desired_length = st.number_input("Desired Length (mm):", min_value=100, max_value=50000, value=7500, step=50)
with col2:
    # Max tolerance in mm (equivalent to 0 to 10cm)
    tolerance_limit = st.slider("Max Allowed Tolerance (mm):", min_value=0, max_value=100, value=50, step=5)

if st.button(f"Calculate Best {selected_profile} Combinations", type="primary"):
    if not available_lengths:
        st.error("Please select at least one available truss length in the sidebar.")
    else:
        with st.spinner("Calculating configurations..."):
            raw_results = find_truss_combinations(desired_length, available_lengths, tolerance_limit)
            
        if raw_results:
            processed_data = []
            for final_len, combo in raw_results:
                diff = final_len - desired_length
                
                # Format combination summary: e.g., "2x (3000mm), 1x (1500mm)"
                counts = {x: combo.count(x) for x in set(combo)}
                summary = ", ".join([f"{counts[k]}x ({k}mm)" for k in sorted(counts.keys(), reverse=True)])
                
                processed_data.append({
                    "Total Length (mm)": final_len,
                    "Deviation": diff,
                    "Abs_Deviation": abs(diff),
                    "Total Pieces": len(combo),
                    "Truss Combination Blueprint": summary
                })
                
            df = pd.DataFrame(processed_data)
            
            # Strict Efficiency Filtering
            df = df.sort_values(by=["Total Length (mm)", "Total Pieces"])
            df = df.drop_duplicates(subset=["Total Length (mm)"], keep="first")
            df = df.sort_values(by=["Abs_Deviation"]).drop(columns=["Abs_Deviation"]).reset_index(drop=True)
            
            # Display Results
            st.success(f"Calculated using {selected_profile} specifications.")
            
            exact_matches = df[df["Deviation"] == 0]
            tolerances = df[df["Deviation"] != 0]
            
            if not exact_matches.empty:
                st.subheader("🎯 Perfect Matches (Fewest Pieces)")
                st.dataframe(exact_matches[["Total Length (mm)", "Truss Combination Blueprint"]], use_container_width=True)
                
            if not tolerances.empty:
                st.subheader("⚖️ Close Matches (Within Tolerance)")
                tolerances["Deviation"] = tolerances["Deviation"].map(lambda x: f"{x:+} mm")
                st.dataframe(tolerances[["Total Length (mm)", "Deviation", "Truss Combination Blueprint"]], use_container_width=True)
                
        else:
            st.error("No structurally viable combinations found within that tolerance using current active stock.")

