import pandas as pd
import re


def generate_suggestions(df):
    
    suggestions = []
        # 1. Detect and suggest repairs for missing values

    for col in df.columns:

        missing_indexes = df.index[df[col].isnull()].tolist()

        if not missing_indexes:
            continue

        # Numeric columns: suggest median
        if pd.api.types.is_numeric_dtype(df[col]):

            suggested_value = df[col].median()

        # Text columns: suggest most frequent value
        else:

            mode_values = df[col].mode(dropna=True)

            if mode_values.empty:
                continue

            suggested_value = mode_values.iloc[0]

        for index in missing_indexes:

            suggestions.append({
                "ID": len(suggestions) + 1,
                "Row": int(index),
                "Column": col,
                "Original Value": "Missing",
                "Suggested Value": suggested_value,
                "Reason": "Missing value replaced using median or most frequent value.",
                "Action": "Fill Missing Value"
            })
    """
    Generate explainable repair suggestions.
    Suggestions are not applied automatically.
    """

    suggestions = []

    # 1. Detect duplicate rows
    duplicate_indexes = df.index[df.duplicated(keep="first")].tolist()

    for index in duplicate_indexes:
        suggestions.append({
            "ID": len(suggestions) + 1,
            "Row": int(index),
            "Column": "Entire Row",
            "Original Value": "Duplicate record",
            "Suggested Value": "Remove duplicate row",
            "Reason": "This row duplicates an earlier record.",
            "Action": "Remove Duplicate"
        })

    # 2. Detect extra spaces in text
    for col in df.select_dtypes(include=["object"]).columns:
        for index, value in df[col].items():

            if pd.isna(value):
                continue

            if isinstance(value, str) and value != value.strip():
                suggestions.append({
                    "ID": len(suggestions) + 1,
                    "Row": int(index),
                    "Column": col,
                    "Original Value": value,
                    "Suggested Value": value.strip(),
                    "Reason": "Extra spaces found around text.",
                    "Action": "Trim Spaces"
                })

    # 3. Standardize common city-name variations
    city_mapping = {
        "bangalore": "Bengaluru",
        "bengaluru": "Bengaluru",
        "mysore": "Mysuru",
        "mysuru": "Mysuru"
    }

    for col in df.select_dtypes(include=["object"]).columns:
        if "city" in str(col).lower():
            for index, value in df[col].items():

                if pd.isna(value):
                    continue

                key = str(value).strip().lower()

                if key in city_mapping:
                    corrected = city_mapping[key]

                    if value != corrected:
                        suggestions.append({
                            "ID": len(suggestions) + 1,
                            "Row": int(index),
                            "Column": col,
                            "Original Value": value,
                            "Suggested Value": corrected,
                            "Reason": "Standardize city-name spelling.",
                            "Action": "Standardize City"
                        })

                            # Detect invalid email addresses

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    for col in df.columns:

        if "email" in str(col).lower():

            for index, value in df[col].items():

                if pd.isna(value):
                    continue

                email = str(value).strip()

                if not re.match(email_pattern, email):
                    suggestions.append({
                        "ID": len(suggestions) + 1,
                        "Row": int(index),
                        "Column": col,
                        "Original Value": value,
                        "Suggested Value": "Manual correction required",
                        "Reason": "Invalid email format detected. Please verify the email address.",
                        "Action": "Validate Email"
                    })
    # Detect numeric outliers using IQR method

    numeric_columns = df.select_dtypes(include=["number"]).columns

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

        outlier_indexes = df.index[
            (df[col] < lower) | (df[col] > upper)
        ]

        for index in outlier_indexes:

            original_value = df.at[index, col]

            if original_value < lower:
                suggested_value = lower
            else:
                suggested_value = upper

            suggestions.append({
                "ID": len(suggestions) + 1,
                "Row": int(index),
                "Column": col,
                "Original Value": original_value,
                "Suggested Value": round(float(suggested_value), 2),
                "Reason": "Unusual numeric value detected using IQR method.",
                "Action": "Treat Outlier"
            })

                # Detect and standardize date formats

    for col in df.columns:

        if "date" in str(col).lower():

            for index, value in df[col].items():

                if pd.isna(value):
                    continue

                try:
                    parsed_date = pd.to_datetime(
                        value,
                        errors="coerce",
                        dayfirst=True
                    )

                    if pd.isna(parsed_date):
                        continue

                    suggested_value = parsed_date.strftime("%Y-%m-%d")

                    original_value = str(value)

                    if original_value != suggested_value:

                        suggestions.append({
                            "ID": len(suggestions) + 1,
                            "Row": int(index),
                            "Column": col,
                            "Original Value": original_value,
                            "Suggested Value": suggested_value,
                            "Reason": "Date format is standardized to YYYY-MM-DD.",
                            "Action": "Standardize Date"
                        })

                except (ValueError, TypeError):
                    continue

                    # Phone Number Validation and Standardization

    for col in df.columns:

        column_name = str(col).lower()

        if any(word in column_name for word in ["phone", "mobile", "telephone", "contact"]):

            for index, value in df[col].items():

                if pd.isna(value):
                    continue

                original_value = str(value).strip()

                # Extract digits only
                digits = re.sub(r"\D", "", original_value)

                # Check Indian mobile number format
                if len(digits) == 10 and digits[0] in "6789":
                    suggested_value = digits

                elif len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
                    suggested_value = "+91 " + digits[2:]

                else:
                    suggestions.append({
                        "ID": len(suggestions) + 1,
                        "Row": int(index),
                        "Column": col,
                        "Original Value": original_value,
                        "Suggested Value": "Manual correction required",
                        "Reason": "Invalid Indian mobile number length or format.",
                        "Action": "Validate Phone"
                    })
                    continue

                if original_value != suggested_value:
                    suggestions.append({
                        "ID": len(suggestions) + 1,
                        "Row": int(index),
                        "Column": col,
                        "Original Value": original_value,
                        "Suggested Value": suggested_value,
                        "Reason": "Phone number formatting standardized.",
                        "Action": "Standardize Phone"
                    })

                        # Detect numbers stored as text

    for col in df.select_dtypes(include=["object"]).columns:

        column_name = str(col).lower()

        # Avoid converting email, phone, date and location columns
        if any(word in column_name for word in
               ["email", "phone", "mobile", "contact",
                "date", "city", "zip", "postal"]):
            continue

        converted_values = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        non_missing = df[col].notna()

        # Convert only when every non-empty value is numeric
        if non_missing.any() and converted_values[non_missing].notna().all():

            for index in df.index[non_missing]:

                original_value = df.at[index, col]
                suggested_value = converted_values.at[index]

                suggestions.append({
                    "ID": len(suggestions) + 1,
                    "Row": int(index),
                    "Column": col,
                    "Original Value": str(original_value),
                    "Suggested Value": suggested_value,
                    "Reason": "Numeric value is stored as text.",
                    "Action": "Correct Data Type"
                })

    # Advanced Business Rule Validation

    for col in df.select_dtypes(include=["number"]).columns:

        column_name = str(col).lower()

        for index, value in df[col].items():

            if pd.isna(value):
                continue

            reason = None

            # Age validation
            if "age" in column_name:
                if value < 0:
                    reason = "Age cannot be negative."
                elif value > 120:
                    reason = "Age exceeds the expected maximum of 120."

            # Salary validation
            elif "salary" in column_name or "income" in column_name:
                if value < 0:
                    reason = "Salary or income cannot be negative."

            # Quantity validation
            elif "quantity" in column_name or "qty" in column_name:
                if value < 0:
                    reason = "Quantity cannot be negative."

            # Marks validation
            elif "mark" in column_name or "score" in column_name:
                if value < 0 or value > 100:
                    reason = "Marks or score is outside the 0-100 range."

            # Price validation
            elif "price" in column_name:
                if value < 0:
                    reason = "Price cannot be negative."

            if reason:
                suggestions.append({
                    "ID": len(suggestions) + 1,
                    "Row": int(index),
                    "Column": col,
                    "Original Value": value,
                    "Suggested Value": "Manual review required",
                    "Reason": reason,
                    "Action": "Review Invalid Value"
                })
    return pd.DataFrame(suggestions)


def apply_repairs(df, suggestions, approved_ids):
    
            
    """
    Apply only suggestions approved by the user.
    Return a repaired copy and a modification log.
    """

    repaired_df = df.copy()
    modification_log = []

    approved = suggestions[
        suggestions["ID"].isin(approved_ids)
    ]

    for _, item in approved.iterrows():

        row = int(item["Row"])
        col = item["Column"]
        action = item["Action"]

        if action == "Remove Duplicate":
            repaired_df = repaired_df.drop(index=row)
        elif action == "Correct Data Type":

            old_value = repaired_df.at[row, col]
            new_value = item["Suggested Value"]

            repaired_df.at[row, col] = new_value

            modification_log.append({
                "Row": row,
                "Column": col,
                 "Action": action,
                "Old Value": str(old_value),
                "New Value": str(new_value),
                "Reason": item["Reason"],
                "Status": "Applied"
            })

        elif action == "Fill Missing Value":

            if row in repaired_df.index:
                old_value = repaired_df.at[row, col]
                new_value = item["Suggested Value"]

                repaired_df.at[row, col] = new_value

                modification_log.append({
                    "Row": row,
                    "Column": col,
                    "Old Value": str(old_value),
                    "New Value": str(new_value),
                    "Reason": item["Reason"],
                    "Status": "Applied"
                })

        elif action in ["Trim Spaces", "Standardize City","Standardize Date", "Standardize Phone"]:
            old_value = repaired_df.at[row, col]
            new_value = item["Suggested Value"]

            repaired_df.at[row, col] = new_value

            modification_log.append({
                "Row": row,
                "Column": col,
                "Old Value": str(old_value),
                "New Value": str(new_value),
                "Reason": item["Reason"],
                "Status": "Applied"
            })

    repaired_df = repaired_df.reset_index(drop=True)
        # Convert approved columns into numeric data types

    corrected_columns = approved.loc[
        approved["Action"] == "Correct Data Type",
        "Column"
    ].unique()

    for col in corrected_columns:
        repaired_df[col] = pd.to_numeric(
            repaired_df[col],
            errors="raise"
        )

    return repaired_df, pd.DataFrame(modification_log)