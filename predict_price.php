<?php
session_start();
if (!isset($_SESSION['user_email'])) {
    header("Location: login.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Predict Future Price</title>
</head>
<body style="display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f9f9f9;">

<div style="background-color: white; padding: 20px; box-shadow: 0px 0px 10px rgba(0,0,0,0.2); width: 320px; text-align: center; border-radius: 10px;">
    <h2>Predict Future Price</h2>

    <label for="product">Select Product:</label>
    <select id="product" required style="width: 100%; padding: 8px; margin-top: 5px;">
        <option value="">-- Select Product --</option>
        <!-- These values must match exactly with your CSV's "Commodities" values -->
        <option value="Onion">Onion</option>
        <option value="Potato">Potato</option>
        <option value="Tomato">Tomato</option>
        <option value="Rice">Rice</option>
        <option value="Wheat">Wheat</option>
        <option value="Atta (Wheat)">Atta (Wheat)</option>
        <option value="Gram Dal">Gram Dal</option>
        <option value="Tur/Arhar Dal">Tur/Arhar Dal</option>
        <option value="Urad Dal">Urad Dal</option>
        <option value="Moong Dal">Moong Dal</option>
        <option value="Masoor Dal">Masoor Dal</option>
        <option value="Groundnut Oil (Packed)">Groundnut Oil (Packed)</option>
        <option value="Mustard Oil (Packed)">Mustard Oil (Packed)</option>
        <option value="Vanaspati (Packed)">Vanaspati (Packed)</option>
        <option value="Soya Oil (Packed)">Soya Oil (Packed)</option>
        <option value="Sunflower Oil (Packed)">Sunflower Oil (Packed)</option>
        <option value="Palm Oil (Packed)">Palm Oil (Packed)</option>
        <option value="Sugar">Sugar</option>
        <option value="Gur">Gur</option>
        <option value="Milk">Milk</option>
        <option value="Tea Loose">Tea Loose</option>
        <option value="Salt Pack (Iodised)">Salt Pack (Iodised)</option>
    </select>

    <br><br>

    <label for="date">Select Date:</label>
    <input type="date" id="date" required style="width: 100%; padding: 8px; margin-top: 5px;">

    <br><br>

    <button onclick="predictPrice()" style="width: 100%; padding: 10px; background-color: #53cadf; color: white; border: none; border-radius: 5px; cursor: pointer;">
        Predict Price
    </button>

    <br><br>

    <p><b>Result:</b> <span id="result">No Prediction Yet</span></p>

    <a href="dashboard.php" style="display: inline-block; margin-top: 10px; padding: 10px 20px; background-color: #53cadf; color: white; border-radius: 5px; text-decoration: none;">Back</a>
</div>

<script>
    async function predictPrice() {
        let product = document.getElementById("product").value;
        let date = document.getElementById("date").value;

        if (!product || !date) {
            alert("Please select both product and date.");
            return;
        }

        try {
            const response = await fetch('http://127.0.0.1:5000/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product: product, date: date })
            });

            const data = await response.json();

            if (response.ok && data.predicted_price !== undefined) {
                document.getElementById("result").innerText = `Predicted Price: ₹${data.predicted_price}`;
            } else {
                document.getElementById("result").innerText = "Error: " + (data.error || "Unknown error occurred");
            }
        } catch (error) {
            console.error("Error during fetch:", error);
            document.getElementById("result").innerText = "⚠️ Failed to connect to prediction service.";
        }
    }
</script>


</body>
</html>



