import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt


# Function to perform RFM Analysis
def perform_rfm_analysis(data):
    # Ensure the columns are correctly named
    required_columns = ['Branch', 'Route', 'Customer', 'Date of Purchase']
    if not all(col in data.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {', '.join(required_columns)}")

    # Convert 'Date of Purchase' to datetime
    data['Date of Purchase'] = pd.to_datetime(data['Date of Purchase'])

    # Calculate Recency, Frequency, and Monetary values
    now = datetime.now()
    rfm = data.groupby('Customer').agg({
        'Date of Purchase': lambda x: (now - x.max()).days,  # Recency
    })
    rfm.columns = ['Recency']

    # Frequency is the count of purchases (based on 'Route')
    frequency = data.groupby('Customer')['Route'].count()

    # Monetary proxy is the count of purchases (based on 'Branch')
    monetary = data.groupby('Customer')['Branch'].count()

    # Add Frequency and Monetary to the RFM dataframe
    rfm['Frequency'] = frequency
    rfm['Monetary'] = monetary

    # Add Branch and Route details to RFM results
    branch_route_details = data.groupby('Customer').agg({
        'Branch': 'first',  # Take the first branch for each customer
        'Route': 'first'  # Take the first route for each customer
    })

    # Merge the branch/route details with the RFM result
    rfm = rfm.merge(branch_route_details, on='Customer', how='left')

    # Assign RFM scores
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[1, 2, 3, 4])
    rfm['F_Score'] = pd.qcut(rfm['Frequency'], 4, labels=[1, 2, 3, 4])
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])

    # Combine the scores into a single RFM score
    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

    # Convert the RFM_Score to integers for categorization
    rfm['RFM_Score_int'] = rfm['RFM_Score'].apply(lambda x: int(x))

    # Categorize customers based on RFM score
    conditions = [
        (rfm['RFM_Score_int'] >= 400),  # Loyal Customers
        (rfm['RFM_Score_int'] >= 300) & (rfm['RFM_Score_int'] < 400),  # Potential Loyalists
        (rfm['RFM_Score_int'] >= 200) & (rfm['RFM_Score_int'] < 300),  # At-Risk Customers
        (rfm['RFM_Score_int'] < 200)  # Lost Customers
    ]
    categories = ['Loyal Customers', 'Potential Loyalists', 'At-Risk Customers', 'Lost Customers']
    categories = ['Lost Customer','At-Risk Customers','Potential Loyalists','Loyal Customer']
    rfm['Category'] = pd.cut(rfm['RFM_Score_int'], bins=[0, 199, 299, 399, 444], labels=categories, include_lowest=True)

    return rfm


# Streamlit UI
st.title("Analysis Tool")
st.write("Upload your dataset and select the analysis you want to perform.")

# Sidebar with buttons for analysis
st.sidebar.title("Select Analysis")
analysis_option = st.sidebar.radio("Choose an analysis to perform", ["None", "RFM Analysis"])

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Read the uploaded file
        data = pd.read_excel(uploaded_file)

        # Perform RFM Analysis if the button is clicked
        if analysis_option == "RFM Analysis":
            # Perform RFM Analysis
            rfm_result = perform_rfm_analysis(data)

            # Display the results
            st.subheader("RFM Analysis Results")
            st.dataframe(rfm_result)

            # Visualization
            st.subheader("RFM Segmentation Distribution")
            fig, ax = plt.subplots()
            rfm_result['RFM_Score'].value_counts().plot(kind='bar', ax=ax)
            ax.set_title("RFM Segmentation")
            ax.set_xlabel("RFM Score")
            ax.set_ylabel("Count")
            st.pyplot(fig)

            # Download button for results
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                rfm_result.to_excel(writer, index=True, sheet_name='RFM Results')
            st.download_button(
                label="Download RFM Results as Excel",
                data=output.getvalue(),
                file_name="rfm_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # Other analysis options can be added here later

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Download template button
if st.button("Download Excel Template"):
    template_data = pd.DataFrame({
        'Branch': ['A', 'B', 'C'],
        'Route': ['X', 'Y', 'Z'],
        'Customer': ['Cust1', 'Cust2', 'Cust3'],
        'Date of Purchase': ['2023-01-01', '2023-02-15', '2023-03-10']
    })
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template_data.to_excel(writer, index=False, sheet_name='Template')
    st.download_button(
        label="Download Excel Template",
        data=output.getvalue(),
        file_name="rfm_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
