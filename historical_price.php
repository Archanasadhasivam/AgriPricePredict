<?php
session_start();
if (!isset($_SESSION['user_email'])) {
    header("Location: login.php");  // Redirect to login if not logged in
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Historical Price Trends</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px; display: flex; justify-content: center; align-items: center; height: 100vh;">

    <div style="border: 1px solid #ccc; padding: 20px; border-radius: 10px; width: 400px; background: #f9f9f9; text-align: center;">
        <h2>View Historical Price Trends</h2>

        <!-- Select Product -->
        <label for="product" style="display: block; text-align: left;">Select Product:</label>
        <select id="product" name="product" style="width: 100%; padding: 8px; margin-bottom: 10px;">
            <option value="onion">Onion</option>
            <option value="potato">Potato</option>
            <option value="tomato">Tomato</option>
            <option value="rice">Rice</option>
            <option value="wheat">Wheat</option>
            <option value="atta (wheat)">Atta (Wheat)</option>
            <option value="gram dal">Gram Dal</option>
            <option value="tur/arhar dal">Tur/Arhar Dal</option>
            <option value="urad dal">Urad Dal</option>
            <option value="moong dal">Moong Dal</option>
            <option value="masoor dal">Masoor Dal</option>
            <option value="groundnut oil (packed)">Groundnut Oil (Packed)</option>
            <option value="mustard oil (packed)">Mustard Oil (Packed)</option>
            <option value="vanaspati (packed)">Vanaspati (Packed)</option>
            <option value="soya oil (packed)">Soya Oil (Packed)</option>
            <option value="sunflower oil (packed)">Sunflower Oil (Packed)</option>
            <option value="palm oil (packed)">Palm Oil (Packed)</option>
            <option value="sugar">Sugar</option>
            <option value="gur">Gur</option>
            <option value="milk">Milk</option>
            <option value="tea loose">Tea Loose</option>
            <option value="salt pack (iodised)">Salt Pack (Iodised)</option>
        </select>

        <!-- Date Inputs -->
        <label for="fromDate" style="display: block; text-align: left;">From:</label>
        <input type="date" id="fromDate" name="fromDate" style="width: 100%; padding: 8px; margin-bottom: 10px;">

        <label for="toDate" style="display: block; text-align: left;">To:</label>
        <input type="date" id="toDate" name="toDate" style="width: 100%; padding: 8px; margin-bottom: 10px;">

        <!-- View Trends Button -->
        <button onclick="fetchPriceTrends()" style="width: 100%; padding: 10px; background-color: #53cadf; color: white; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 20px;">
            View Trends
        </button>

        <!-- Result Table -->
        <table border="1" width="100%" style="margin-top: 20px; text-align: center;" id="resultTable">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Price (per kg)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="2">No Data Available</td>
                </tr>
            </tbody>
        </table>

        <!-- Back Button -->
        <a href="dashboard.php" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #53cadf; color: white; border-radius: 5px; text-decoration: none;">Back</a>
    </div>

    <script>
        function fetchPriceTrends() {
            const product = document.getElementById("product").value;
            const fromDate = document.getElementById("fromDate").value;
            const toDate = document.getElementById("toDate").value;
            const resultTable = document.getElementById("resultTable").getElementsByTagName('tbody')[0];

            if (!fromDate || !toDate) {
                alert("Please select both dates.");
                return;
            }

            fetch(`http://127.0.0.1:5000/price_trend?product_name=${product}&from_date=${fromDate}&to_date=${toDate}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }

                    // Clear previous results
                    resultTable.innerHTML = "";

                    // Populate table with new data
                    data.forEach(item => {
                        let row = resultTable.insertRow();
                        let dateCell = row.insertCell(0);
                        let priceCell = row.insertCell(1);
                        dateCell.textContent = new Date(item.date).toISOString().split('T')[0];  // Format date
                        priceCell.textContent = item.price;
                    });
                })
                .catch(error => {
                    console.error("Error fetching data:", error);
                });
        }
    </script>
</body>
</html>