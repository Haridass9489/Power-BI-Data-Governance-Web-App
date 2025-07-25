import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px
from utils import get_cached_workspace_data, apply_sidebar_style, show_workspace
from utils import  render_profile_header, add_logout_button

apply_sidebar_style()
def inject_external_style():
    with open("static/style.css") as f:
        css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
inject_external_style()

if not (st.session_state.get("access_token") and
        st.session_state.get("user_email")):
    st.warning("🔐 Authentication Required")
    st.stop()

add_logout_button()
render_profile_header()
show_workspace()

col1, col2, col3 = st.columns(3)
with col2:
    st.image("./images/dover_log.png")

st.markdown("<h1 style='text-align: center;'>👥 Users</h1>", unsafe_allow_html=True)
# Dashboard Description
st.markdown("""
<div style='text-align: center; font-size: 1.05rem; background-color: #E7DBF3; padding: 14px 24px; border-left: 6px solid #673ab7; border-radius: 8px; margin-bottom: 25px;'>
This dashboard offers a detailed overview of user access across selected Power BI workspaces.
You can explore user roles, identify access patterns based on email domains, and analyze distribution of administrative privileges.
</div><hr>
""", unsafe_allow_html=True)

token = st.session_state.access_token
workspace_ids = st.session_state.workspace_ids
email = st.session_state.user_email
workspace_map = {v: k for k, v in st.session_state.workspace_options.items()}

# Fetch user data across multiple workspaces
users_df_list = []
for ws_id in workspace_ids:
    reports, datasets, users = get_cached_workspace_data(token, ws_id, email)

    users["workspace_id"] = ws_id
    users["workspace_name"] = workspace_map.get(ws_id, "Unknown")
    users_df_list.append(users)

users_df = pd.concat(users_df_list, ignore_index=True)

if users_df.empty:
    st.warning("📭 No user data found across selected workspaces.")
    st.stop()

# Display number of users per workspace
st.markdown("##  Number of Users per Workspace")
workspace_user_counts = users_df["workspace_name"].value_counts().reset_index()
workspace_user_counts.columns = ["Workspace", "Number of Users"]
st.dataframe(workspace_user_counts, use_container_width=True)

col1, col2 = st.columns([4,5])
with col1:
    st.subheader("📊 Group User Access Rights")
    role_counts = users_df["groupUserAccessRight"].value_counts()
    labels = role_counts.index
    sizes = role_counts.values
    role_colors = {
        "Admin": "OrangeRed",
        "Contributor": "DodgerBlue",
        "Viewer": "DimGray",
        "Member": "MediumSeaGreen"
    }
    colors = [role_colors.get(role, "LightGray") for role in labels]

    fig, ax = plt.subplots(figsize=(4, 3.5))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.3),
        textprops={'fontsize': 8}
    )
    ax.set_title("Group Access Rights", fontsize=10)
    ax.axis("equal")
    st.pyplot(fig)

with col2:
    st.subheader("🌍 Workspace Access by Email Domain")
    users_df["Domain"] = users_df["emailAddress"].str.split("@").str[-1]
    domain_counts = users_df["Domain"].value_counts().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(4.2, 3))
    ax.set_title("Access by Email Domain")
    sns.barplot(x=domain_counts.values, y=domain_counts.index, palette=["SkyBlue"] * len(domain_counts), ax=ax)
    st.pyplot(fig)

st.subheader("🌐 Email Domain Distribution by Workspace")

users_df["Domain"] = users_df["emailAddress"].str.split("@").str[-1]

treemap_df = (
    users_df.groupby(["workspace_name", "Domain"])
    .size()
    .reset_index(name="User Count")
)

fig = px.treemap(
    treemap_df,
    path=["workspace_name", "Domain"],
    values="User Count",
    color="User Count",
    color_continuous_scale="Blues"
)
st.plotly_chart(fig, use_container_width=True)


# Buttons for displaying user table or dataframe
if "veiw_users" not in st.session_state:
    st.session_state.veiw_users = False
if "Explore_users_dataframe" not in st.session_state:
    st.session_state.Explore_users_dataframe = False

with st.container():
    col1, col2, col3, col4, col5 = st.columns([1,3,3,4,1])
    with col2:
        if st.button("📄 View Users"):
            st.session_state.veiw_users = True
            st.session_state.Explore_users_dataframe = False
    with col4:
        if st.button("📄 Explore Users DataFrame"):
            st.session_state.veiw_users = False
            st.session_state.Explore_users_dataframe = True
if st.session_state.veiw_users:
    for ws_name, group in users_df.groupby("workspace_name"):
        group = group.reset_index(drop=True)  
        st.markdown(f"### 📍 Workspace: `{ws_name}` ({len(group)} users)")
        st.markdown('<div class="classic-table">', unsafe_allow_html=True)
        st.markdown('<div class="classic-row header">', unsafe_allow_html=True)
        header1, header2, header3, header4, header5, header6 = st.columns([1, 3, 4, 3, 2,3])
        header1.markdown("🔖 ID")
        header2.markdown("📛 Name")
        header3.markdown("👤 Email")
        header4.markdown("👥 Access Rights")
        header5.markdown("🏷️ Type")
        header6.markdown("🏢 Workspace")

        for idx, row in group.iterrows():
            st.markdown('<div class="classic-row">', unsafe_allow_html=True)
            col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 4, 3, 2,3])
            col1.markdown(f"**{idx + 1}**")
            col2.markdown(f"**{row['displayName']}**")
            col3.markdown(f"`{row['emailAddress']}`")
            col4.markdown(f"**{row['groupUserAccessRight']}**")
            col5.markdown(f"**{row['principalType']}**")
            col6.markdown(f"`{row['workspace_name']}`")

if st.session_state.Explore_users_dataframe:
    st.markdown("## 📊 Full Users Table by Workspace")
    for ws_name, group in users_df.groupby("workspace_name"):
        
        # Reset index for clean table
        group = group.reset_index(drop=True)

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"### 🏢 Workspace: `{ws_name}`")
        with col2:
            csv = group.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{ws_name}_user_activity.csv",
                mime="text/csv"
            )

        st.dataframe(group[["emailAddress", "groupUserAccessRight", "displayName", "workspace_name"]])