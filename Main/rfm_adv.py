import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

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
        'Route': 'count',  # Frequency
        'Branch': 'count'  # Monetary proxy (replace with actual value if available)
    })
    rfm.columns = ['Recency', 'Frequency', 'Monetary']

    # Assign RFM scores
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])  # Lower recency = higher score
    rfm['F_Score'] = pd.qcut(rfm['Frequency'], 4, labels=[1, 2, 3, 4])  # Higher frequency = higher score
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])  # Higher monetary = higher score
    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)

    # Define customer segmentation
    rfm['Segment'] = np.select(
        [
            (rfm['R_Score'] == '1') & (rfm['F_Score'] == '4') & (rfm['M_Score'] == '4'),
            (rfm['R_Score'] == '1') & (rfm['F_Score'] == '4') & (rfm['M_Score'] == '3'),
            (rfm['R_Score'] == '1') & (rfm['F_Score'] == '3') & (rfm['M_Score'] == '3'),
            (rfm['R_Score'] == '1') & (rfm['F_Score'] == '2') & (rfm['M_Score'] == '2'),
            (rfm['R_Score'] == '1') & (rfm['F_Score'] == '1') & (rfm['M_Score'] == '1'),
            (rfm['R_Score'] == '2') & (rfm['F_Score'] == '2') & (rfm['M_Score'] == '2'),
            (rfm['R_Score'] == '3') & (rfm['F_Score'] == '3') & (rfm['M_Score'] == '3'),
            (rfm['R_Score'] == '4') & (rfm['F_Score'] == '4') & (rfm['M_Score'] == '4')
        ],
        [
            'Best Customers',
            'Loyal Customers',
            'Potential Loyalists',
            'Recent Customers',
            'Lost Customers',
            'At Risk',
            'Churned',
            'New Customers'
        ],
        default='Other'
    )

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

            # Add a selectbox to choose a customer for detailed analysis
            customer_names = rfm_result.index.tolist()
            selected_customer = st.selectbox("Select a customer to view details", customer_names)

            if selected_customer:
                st.write(f"Selected Customer: {selected_customer}")
                st.write(rfm_result.loc[selected_customer])

                # Show customer details when a customer is selected
                st.subheader("Customer's Transaction Details")
                customer_data = data[data['Customer'] == selected_customer]
                st.dataframe(customer_data)

                # Show additional charts for the customer
                st.subheader("Customer's Purchase Trend")
                fig, ax = plt.subplots()
                customer_data.groupby('Date of Purchase').size().plot(kind='line', ax=ax)
                ax.set_title(f"Purchase Trend for {selected_customer}")
                ax.set_xlabel("Date of Purchase")
                ax.set_ylabel("Number of Purchases")
                st.pyplot(fig)

                # Show customer's monetary value chart
                st.subheader("Customer's Purchase Monetary Value")
                fig, ax = plt.subplots()
                customer_data.groupby('Date of Purchase')['Branch'].sum().plot(kind='line', ax=ax)
                ax.set_title(f"Monetary Value Trend for {selected_customer}")
                ax.set_xlabel("Date of Purchase")
                ax.set_ylabel("Monetary Value")
                st.pyplot(fig)

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
