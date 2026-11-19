import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re

from repair import generate_suggestions, apply_repairs


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="DataFix | Intelligent Data Quality Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "data" not in st.session_state:
    st.session_state["data"] = None

if "repaired_data" not in st.session_state:
    st.session_state["repaired_data"] = None

if "modification_log" not in st.session_state:
    st.session_state["modification_log"] = pd.DataFrame()

if "uploaded_file_key" not in st.session_state:
    st.session_state["uploaded_file_key"] = None

if "manual_corrections" not in st.session_state:
    st.session_state["manual_corrections"] = set()


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #F4F7FB;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #16325C;
    margin-bottom: 5px;
}

.sub-title {
    font-size: 16px;
    color: #64748B;
    margin-bottom: 25px;
}

h1, h2, h3 {
    color: #16325C;
    font-weight: 700;
}

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.04);
}

.stButton > button {
    background-color: #2563EB;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 8px 18px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #1D4ED8;
    color: white;
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

section[data-testid="stSidebar"] {
    background-color: #EAF0F8;
}

[data-testid="stFileUploader"] {
    background-color: white;
    border: 1px dashed #94A3B8;
    border-radius: 12px;
    padding: 15px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.title("🛡️ DataFix")

st.sidebar.caption(
    "Autonomous Data Quality & Repair Engine"
)

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Dashboard", "About Project"]
)

st.sidebar.markdown("---")

st.sidebar.info(
    "Upload → Detect → Diagnose → Repair → Validate"
)


# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

def load_dataset(file):

    if file.name.endswith(".csv"):
        return pd.read_csv(file)

    elif file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)

    return None


# --------------------------------------------------
# DETECT DATA QUALITY ISSUES
# --------------------------------------------------

def detect_issues(df):

    issues = {}

    issues["Missing Values"] = int(
        df.isnull().sum().sum()
    )

    issues["Duplicate Rows"] = int(
        df.duplicated().sum()
    )

    # Invalid Emails

    email_columns = [
        col for col in df.columns
        if "email" in str(col).lower()
    ]

    invalid_emails = 0

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    for col in email_columns:

        for value in df[col].dropna():

            if not re.match(
                email_pattern,
                str(value).strip()
            ):
                invalid_emails += 1

    issues["Invalid Emails"] = invalid_emails

    # Numeric Outliers

    outliers = 0

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns

    for col in numeric_columns:

        values = df[col].dropna()

        if len(values) < 4:
            continue

        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers += int(
            ((values < lower) | (values > upper)).sum()
        )

    issues["Possible Numeric Outliers"] = outliers

    # Business Rule Validation

    business_rule_issues = 0

    for col in df.select_dtypes(include=["number"]).columns:

        column_name = str(col).lower()

        for value in df[col].dropna():

            invalid = False

            if "age" in column_name:
                if value < 0 or value > 120:
                    invalid = True

            elif "salary" in column_name or "income" in column_name:
                if value < 0:
                    invalid = True

            elif "quantity" in column_name or "qty" in column_name:
                if value < 0:
                    invalid = True

            elif "mark" in column_name or "score" in column_name:
                if value < 0 or value > 100:
                    invalid = True

            elif "price" in column_name:
                if value < 0:
                    invalid = True

            if invalid:
                business_rule_issues += 1

    issues["Business Rule Violations"] = business_rule_issues

    return issues


# --------------------------------------------------
# CALCULATE DATA QUALITY SCORE
# --------------------------------------------------

def calculate_quality_score(df):

    if df.empty or df.size == 0:
        return 0

    total_cells = df.size

    missing_cells = df.isnull().sum().sum()

    duplicate_rows = df.duplicated().sum()

    total_issues = (
        missing_cells +
        (duplicate_rows * len(df.columns))
    )

    score = 100 - (
        total_issues / total_cells * 100
    )

    return round(max(0, score), 2)


# --------------------------------------------------
# POST-REPAIR VALIDATION
# --------------------------------------------------

def validate_dataset(df):

    issues = detect_issues(df)

    total_issues = sum(issues.values())

    if total_issues == 0:
        status = "Passed"
    else:
        status = "Needs Attention"

    validation_report = pd.DataFrame({

        "Validation Check": list(issues.keys()),

        "Remaining Issues": list(issues.values())

    })

    return validation_report, status


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

if page == "Home":

    st.markdown(
        """
<div style="background:white; padding:25px; border-radius:14px;
            border:1px solid #E2E8F0; margin-bottom:20px;">

<h2 style="color:#16325C; margin-bottom:10px;">
Welcome to DataFix 👋
</h2>

<p style="color:#64748B; font-size:16px;">
Transform raw datasets into clean, reliable and
high-quality data using intelligent validation
and automated repair recommendations.
</p>

<p style="color:#2563EB; font-weight:600;">
Upload your dataset and start improving data quality.
</p>

</div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
<div style="background:white; padding:22px;
            border-radius:12px; border-left:5px solid #2563EB;
            min-height:120px;">

<h3>🔍 Smart Detection</h3>

<p style="color:#64748B;">
Identify missing values, duplicates, invalid formats,
outliers and business rule violations.
</p>

</div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
<div style="background:white; padding:22px;
            border-radius:12px; border-left:5px solid #16A34A;
            min-height:120px;">

<h3>🛠️ Intelligent Repair</h3>

<p style="color:#64748B;">
Review repair recommendations, approve changes
and manually correct invalid records.
</p>

</div>
            """,
            unsafe_allow_html=True
        )

    # PLATFORM CAPABILITIES

    st.markdown("---")

    st.markdown("## 🚀 DataFix Platform Capabilities")

    feature_col1, feature_col2, feature_col3 = st.columns(3)

    with feature_col1:

        st.markdown("### 🔍 Detection")

        st.write("""
        - Missing values
        - Duplicate records
        - Invalid emails
        - Numeric outliers
        - Business rule violations
        """)

    with feature_col2:

        st.markdown("### 🛠️ Correction")

        st.write("""
        - Automated repair suggestions
        - User-approved repairs
        - Manual data correction
        - Data standardization
        - Type correction
        """)

    with feature_col3:

        st.markdown("### 📊 Analytics")

        st.write("""
        - Data quality score
        - Before-and-after analysis
        - Repair history
        - Data profiling
        - Downloadable reports
        """)

    # DATASET UPLOAD

    st.markdown("---")

    st.markdown("""
    <h2 style="color:#16325C;">
        📂 Upload Your Dataset
    </h2>

    <p style="color:#64748B;">
        Supported formats: CSV, XLSX and XLS.
        Upload your file to begin intelligent data analysis.
    </p>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:

        try:

            file_key = (
                uploaded_file.name,
                uploaded_file.size
            )

            if st.session_state["uploaded_file_key"] != file_key:

                df = load_dataset(uploaded_file)

                st.session_state["data"] = df
                st.session_state["repaired_data"] = None
                st.session_state["modification_log"] = pd.DataFrame()
                st.session_state["manual_corrections"] = set()
                st.session_state["uploaded_file_key"] = file_key

            df = st.session_state["data"]

            if df is None:

                st.error("Unsupported file format.")

            else:

                st.success("Dataset uploaded successfully!")

                st.write("### Dataset Preview")

                st.dataframe(
                    df.head(10),
                    use_container_width=True
                )

                st.write(
                    f"**Rows:** {df.shape[0]} | "
                    f"**Columns:** {df.shape[1]}"
                )

                if st.button("Analyze Dataset"):

                    st.session_state["analyzed"] = True

                    st.success(
                        "Analysis completed! Open the Dashboard."
                    )

        except Exception as e:

            st.error(f"Unable to read this file: {e}")


# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------

elif page == "Dashboard":

    st.title("📊 Data Quality Dashboard")

    if st.session_state["data"] is None:

        st.warning(
            "Please upload a dataset from the Home page first."
        )

    else:

        df = st.session_state["data"]

        # WORKING DATASET

        working_df = st.session_state["repaired_data"]

        if working_df is None:
            working_df = df.copy()

        # DETECT ISSUES

        issues = detect_issues(working_df)

        total_records = len(working_df)

        total_columns = len(working_df.columns)

        total_missing = issues["Missing Values"]

        total_duplicates = issues["Duplicate Rows"]

        # DATASET OVERVIEW

        st.markdown("### Dataset Overview")

        quality_score = calculate_quality_score(working_df)

        st.metric(
            label="Data Quality Score",
            value=f"{quality_score}/100"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Records", total_records)

        c2.metric("Total Columns", total_columns)

        c3.metric("Missing Values", total_missing)

        c4.metric("Duplicate Rows", total_duplicates)

        st.markdown("---")

        # DETECTED ISSUES

        st.subheader("Detected Data Quality Issues")

        col1, col2 = st.columns(2)

        with col1:

            st.dataframe(
                pd.DataFrame(
                    list(issues.items()),
                    columns=["Issue Type", "Count"]
                ),
                use_container_width=True,
                hide_index=True
            )

        with col2:

            fig, ax = plt.subplots(figsize=(6, 4))

            ax.bar(
                list(issues.keys()),
                list(issues.values())
            )

            ax.set_title("Data Quality Issues")

            ax.set_ylabel("Number of Issues")

            ax.tick_params(
                axis="x",
                rotation=35
            )

            plt.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

        st.markdown("---")

        # SMART ERROR EXPLANATION

        st.subheader("🤖 Smart Data Quality Explanation")

        explanations = {

            "Missing Values": {
                "reason": "Some records contain empty or unavailable information.",
                "impact": "Missing values can affect calculations, reporting and machine learning models.",
                "action": "Review the affected columns and fill missing values using suitable methods."
            },

            "Duplicate Rows": {
                "reason": "Identical records appear more than once in the dataset.",
                "impact": "Duplicates can inflate totals and produce inaccurate analysis.",
                "action": "Review duplicate records and remove unnecessary repetitions."
            },

            "Invalid Emails": {
                "reason": "Some email addresses do not match the expected email format.",
                "impact": "Incorrect email formats can cause communication and data integration problems.",
                "action": "Review and correct the email addresses."
            },

            "Possible Numeric Outliers": {
                "reason": "Some numeric values fall outside the expected IQR range.",
                "impact": "Extreme values may influence averages, charts and statistical models.",
                "action": "Investigate the values before deciding whether to correct or retain them."
            },

            "Business Rule Violations": {
                "reason": "Some values do not follow expected business rules.",
                "impact": "Invalid values may cause inaccurate reports and business decisions.",
                "action": "Review and correct the values using verified source information."
            }
        }

        for issue_name, issue_count in issues.items():

            if issue_count > 0:

                with st.expander(
                    f"⚠️ {issue_name}: {issue_count} detected"
                ):

                    details = explanations[issue_name]

                    st.write("**Possible Reason:**")
                    st.write(details["reason"])

                    st.write("**Potential Impact:**")
                    st.write(details["impact"])

                    st.write("**Recommended Action:**")
                    st.info(details["action"])

        if sum(issues.values()) == 0:

            st.success(
                "No data quality issues detected. "
                "Your dataset passed the current checks."
            )

        # COLUMN-WISE MISSING VALUE ANALYSIS

        st.subheader("Column-wise Missing Value Analysis")

        missing_by_column = working_df.isnull().sum()

        missing_df = pd.DataFrame({

            "Column": missing_by_column.index,

            "Missing Values": missing_by_column.values

        })

        st.dataframe(
            missing_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        # SMART DATASET INSIGHTS

        st.subheader("🧠 Smart Dataset Insights")

        memory_usage = (
            working_df.memory_usage(deep=True).sum() / 1024
        )

        missing_by_column = working_df.isnull().sum()

        if len(missing_by_column) > 0:

            highest_missing_column = missing_by_column.idxmax()

            highest_missing_count = missing_by_column.max()

        else:

            highest_missing_column = "N/A"

            highest_missing_count = 0

        duplicate_value_columns = []

        for col in working_df.columns:

            if working_df[col].duplicated().sum() > 0:

                duplicate_value_columns.append(str(col))

        unique_counts = working_df.nunique()

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Dataset Memory Usage",
                f"{memory_usage:.2f} KB"
            )

            st.metric(
                "Total Unique Values",
                int(unique_counts.sum())
            )

        with col2:

            st.metric(
                "Total Duplicate Rows",
                int(working_df.duplicated().sum())
            )

            st.metric(
                "Total Columns",
                len(working_df.columns)
            )

        st.markdown("### Automatic Observations")

        if highest_missing_count > 0:

            st.warning(
                f"Column '{highest_missing_column}' has the "
                f"highest missing values: {highest_missing_count}."
            )

        else:

            st.success("No missing values detected in any column.")

        if duplicate_value_columns:

            st.info(
                "Repeated values detected in: "
                + ", ".join(duplicate_value_columns)
            )

        else:

            st.success(
                "No repeated values detected in individual columns."
            )

        if not unique_counts.empty:

            highest_unique_column = unique_counts.idxmax()

            st.write(
                f"Column with the highest number of unique values: "
                f"**{highest_unique_column}** "
                f"({unique_counts[highest_unique_column]} unique values)."
            )

        unique_df = pd.DataFrame({

            "Column": unique_counts.index,

            "Unique Values": unique_counts.values

        })

        st.markdown("### Unique Value Analysis")

        st.dataframe(
            unique_df,
            use_container_width=True,
            hide_index=True
        )

        # DATASET PREVIEW

        st.subheader("Dataset Preview")

        st.dataframe(
            working_df,
            use_container_width=True
        )

        # DATA PROFILING

        st.markdown("---")

        st.subheader("🔬 Data Profiling Dashboard")

        profiling_data = []

        for col in working_df.columns:

            profiling_data.append({

                "Column": col,

                "Data Type": str(working_df[col].dtype),

                "Non-Null Values": int(working_df[col].count()),

                "Missing Values": int(working_df[col].isnull().sum()),

                "Unique Values": int(working_df[col].nunique()),

                "Minimum": (
                    str(working_df[col].min())
                    if pd.api.types.is_numeric_dtype(working_df[col])
                    and working_df[col].notna().any()
                    else "N/A"
                ),

                "Maximum": (
                    str(working_df[col].max())
                    if pd.api.types.is_numeric_dtype(working_df[col])
                    and working_df[col].notna().any()
                    else "N/A"
                ),

                "Average": (
                    round(working_df[col].mean(), 2)
                    if pd.api.types.is_numeric_dtype(working_df[col])
                    and working_df[col].notna().any()
                    else "N/A"
                )

            })

        profiling_df = pd.DataFrame(profiling_data)

        st.dataframe(
            profiling_df,
            use_container_width=True,
            hide_index=True
        )

        # STATISTICAL SUMMARY

        st.markdown("### 📊 Statistical Summary")

        numeric_df = working_df.select_dtypes(
            include=np.number
        )

        if not numeric_df.empty:

            st.dataframe(
                numeric_df.describe().round(2),
                use_container_width=True
            )

        else:

            st.info(
                "No numeric columns available for statistical analysis."
            )

        # DOWNLOAD ORIGINAL DATASET

        st.download_button(
            label="Download Original Dataset",

            data=df.to_csv(
                index=False
            ).encode("utf-8"),

            file_name="original_dataset.csv",

            mime="text/csv"
        )

        st.markdown("---")

        # DATA REPAIR ENGINE

        st.title("🛠️ Data Repair Engine")

        st.write(
            "Review the suggested corrections and approve "
            "the changes you want to apply."
        )

        suggestions = generate_suggestions(working_df)

        if not suggestions.empty:

            st.subheader("Repair Suggestions")

            st.dataframe(
                suggestions,
                use_container_width=True,
                hide_index=True
            )

            approved_ids = st.multiselect(
                "Select suggestions to approve:",
                options=suggestions["ID"].tolist()
            )

            if st.button("Apply Approved Repairs"):

                repaired_df, modification_log = apply_repairs(
                    working_df,
                    suggestions,
                    approved_ids
                )

                st.session_state["repaired_data"] = repaired_df

                st.session_state["modification_log"] = modification_log

                st.session_state["manual_corrections"] = set()

                st.success(
                    "Approved repairs applied successfully!"
                )

                st.rerun()

        else:

            st.success("No repair suggestions found!")

        # MANUAL DATA CORRECTION

        if not suggestions.empty:

            review_suggestions = suggestions[
                suggestions["Action"] == "Review Invalid Value"
            ]

        else:

            review_suggestions = pd.DataFrame()

        if not review_suggestions.empty:

            st.markdown("---")

            st.subheader("Manual Data Correction")

            st.info(
                "Review invalid values and enter the correct values manually."
            )

            available_reviews = review_suggestions[
                ~review_suggestions["ID"].isin(
                    st.session_state["manual_corrections"]
                )
            ]

            if not available_reviews.empty:

                selected_id = st.selectbox(
                    "Select invalid value to correct:",
                    available_reviews["ID"].tolist()
                )

                selected_item = available_reviews[
                    available_reviews["ID"] == selected_id
                ].iloc[0]

                row = selected_item["Row"]

                col = selected_item["Column"]

                st.write("Column:", col)

                st.write(
                    "Current Value:",
                    working_df.loc[row, col]
                )

                corrected_value = st.text_input(
                    "Enter the correct value:"
                )

                if st.button("Apply Manual Correction"):

                    try:

                        current_df = st.session_state[
                            "repaired_data"
                        ]

                        if current_df is None:
                            current_df = df.copy()

                        else:
                            current_df = current_df.copy()

                        if pd.api.types.is_numeric_dtype(df[col]):

                            corrected_value = pd.to_numeric(
                                corrected_value,
                                errors="raise"
                            )

                        old_value = current_df.loc[row, col]

                        current_df.loc[row, col] = corrected_value

                        st.session_state["repaired_data"] = current_df

                        st.session_state["manual_corrections"].add(
                            selected_id
                        )

                        new_log = pd.DataFrame([{

                            "Row": row,

                            "Column": col,

                            "Action": "Manual Correction",

                            "Old Value": old_value,

                            "New Value": corrected_value,

                            "Reason": "User manually corrected invalid value",

                            "Status": "Applied"

                        }])

                        st.session_state["modification_log"] = pd.concat(
                            [
                                st.session_state["modification_log"],
                                new_log
                            ],
                            ignore_index=True
                        )

                        st.success(
                            f"{col} corrected successfully!"
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(f"Correction failed: {e}")

            else:

                st.success(
                    "All displayed manual correction suggestions have been addressed."
                )

        # DISPLAY REPAIRED DATASET

        if st.session_state["repaired_data"] is not None:

            repaired_df = st.session_state["repaired_data"]

            st.markdown("---")

            # DATA QUALITY IMPROVEMENT SUMMARY

            st.subheader("📈 Data Quality Improvement Summary")

            before_issues = sum(
                detect_issues(df).values()
            )

            after_issues = sum(
                detect_issues(repaired_df).values()
            )

            issues_fixed = max(
                0,
                before_issues - after_issues
            )

            improvement = (
                (issues_fixed / before_issues) * 100
                if before_issues > 0 else 0
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Issues Before Repair",
                    before_issues
                )

            with col2:

                st.metric(
                    "Issues After Repair",
                    after_issues
                )

            col3, col4 = st.columns(2)

            with col3:

                st.metric(
                    "Total Issues Fixed",
                    issues_fixed
                )

            with col4:

                st.metric(
                    "Improvement Percentage",
                    f"{improvement:.2f}%"
                )

            comparison_data = pd.DataFrame({

                "Status": [
                    "Before Repair",
                    "After Repair"
                ],

                "Total Issues": [
                    before_issues,
                    after_issues
                ]

            })

            st.markdown("### Before vs After Issue Comparison")

            st.bar_chart(
                comparison_data.set_index("Status")
            )

            st.markdown("---")

            # POST-REPAIR VALIDATION

            st.subheader("✅ Post-Repair Validation Report")

            validation_report, validation_status = validate_dataset(
                repaired_df
            )

            if validation_status == "Passed":

                st.success(
                    "All validation checks passed! "
                    "No remaining issues detected."
                )

            else:

                st.warning(
                    "Some data quality issues still remain. "
                    "Please review the report."
                )

            st.dataframe(
                validation_report,
                use_container_width=True,
                hide_index=True
            )

            # DOWNLOAD VALIDATION REPORT

            st.download_button(

                label="📥 Download Validation Report",

                data=validation_report.to_csv(
                    index=False
                ).encode("utf-8"),

                file_name="datafix_validation_report.csv",

                mime="text/csv"
            )

            st.markdown("---")

            # REPAIRED DATASET

            st.subheader("Repaired Dataset")

            st.dataframe(
                repaired_df,
                use_container_width=True
            )

            # QUALITY SCORE COMPARISON

            st.markdown("---")

            st.subheader("Quality Improvement Comparison")

            before_score = calculate_quality_score(df)

            after_score = calculate_quality_score(repaired_df)

            col1, col2 = st.columns(2)

            col1.metric(
                "Before Repair",
                f"{before_score}/100"
            )

            col2.metric(
                "After Repair",
                f"{after_score}/100",
                delta=f"{after_score - before_score:.2f} points"
            )

            # MODIFICATION HISTORY

            st.markdown("---")

            st.subheader("Modification History")

            modification_log = st.session_state[
                "modification_log"
            ]

            # REPAIR HISTORY ANALYTICS

            st.markdown("---")

            st.subheader("📊 Repair History Analytics")

            if not modification_log.empty:

                total_modifications = len(modification_log)

                st.metric(
                    "Total Modifications",
                    total_modifications
                )

                if "Action" in modification_log.columns:

                    repair_counts = (
                        modification_log["Action"]
                        .value_counts()
                        .reset_index()
                    )

                    repair_counts.columns = [
                        "Repair Type",
                        "Count"
                    ]

                    st.dataframe(
                        repair_counts,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.bar_chart(
                        repair_counts.set_index("Repair Type")
                    )

                else:

                    st.info(
                        "Repair type information is not available "
                        "in the modification log."
                    )

                st.dataframe(
                    modification_log,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No modification data available for analytics."
                )

            # DOWNLOAD REPAIRED DATASET

            st.markdown("---")

            st.download_button(

                label="Download Repaired Dataset",

                data=repaired_df.to_csv(
                    index=False
                ).encode("utf-8"),

                file_name="repaired_dataset.csv",

                mime="text/csv"
            )

            # COMPLETE QUALITY REPORT

            st.markdown("---")

            st.subheader("📑 Complete Data Quality Report")

            complete_report = pd.DataFrame({

                "Metric": [
                    "Original Quality Score",
                    "Repaired Quality Score",
                    "Issues Before Repair",
                    "Issues After Repair",
                    "Total Issues Fixed",
                    "Improvement Percentage"
                ],

                "Result": [
                    f"{before_score}/100",
                    f"{after_score}/100",
                    before_issues,
                    after_issues,
                    issues_fixed,
                    f"{improvement:.2f}%"
                ]

            })

            st.dataframe(
                complete_report,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(

                label="📥 Download Complete Quality Report",

                data=complete_report.to_csv(
                    index=False
                ).encode("utf-8"),

                file_name="datafix_complete_quality_report.csv",

                mime="text/csv"
            )


# --------------------------------------------------
# ABOUT PROJECT PAGE
# --------------------------------------------------

elif page == "About Project":

    st.title("About DataFix")

    st.write("""
    DataFix is designed to improve dataset reliability by detecting
    common data quality problems and supporting safe, explainable repairs.
    """)

    st.subheader("Core Capabilities")

    st.markdown("""
    1. **Detect:** Identify missing values, duplicates and invalid entries.

    2. **Diagnose:** Understand possible reasons for data errors.

    3. **Repair:** Recommend appropriate corrections.

    4. **Validate:** Recheck the dataset after corrections.

    5. **Explain:** Show why each correction is suggested.

    6. **Track:** Maintain a history of approved modifications.
    """)

    st.success(
        "Built for Trust: Show what changed, why it changed "
        "and how the repaired dataset was validated."
    )

    st.markdown("---")

    st.caption(
        "INNOVEDGE HACKATHON 2026 | DataFix Project"
    )