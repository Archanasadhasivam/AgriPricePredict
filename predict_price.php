<?php
session_start();

// Redirect to login if user is not authenticated
if (!isset($_SESSION['user_email'])) {
    header("Location: login.php");
    exit();
}

// Include database connection (assuming db_connect.php exists and is configured for Aiven)
include('db_connect.php');

$user_email = $_SESSION['user_email'];

// Optional: Fetch user information for personalization
$username = 'User';
if (isset($_SESSION['user_id'])) {
    $user_id = $_SESSION['user_id'];
    $stmt = $conn->prepare("SELECT username FROM users WHERE id = ?");
    $stmt->bind_param("i", $user_id);
    $stmt->execute();
    $result = $stmt->get_result();
    if ($row = $result->fetch_assoc()) {
        $username = htmlspecialchars($row['username']);
    }
    $stmt->close();
}

$prediction_result = null;
$error_message = null;
$products = [];

// Fetch list of all unique products for the dropdown (from historical_prices table)
$productQuery = "SELECT DISTINCT product_name FROM historical_prices ORDER BY product_name ASC";
$productResult = $conn->query($productQuery);
while ($row = $productResult->fetch_assoc()) {
    $products[] = $row['product_name'];
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $product_name = isset($_POST['product_name']) ? htmlspecialchars($_POST['product_name']) : '';
    $prediction_date = isset($_POST['prediction_date']) ? htmlspecialchars($_POST['prediction_date']) : '';

    if (!empty($product_name) && !empty($prediction_date)) {
        // Call the Python Flask API to get the prediction
        $api_url = 'http://localhost:5000/predict'; // Adjust if your Flask app is on a different host/port
        $post_data = array('product' => $product_name, 'date' => $prediction_date);

        $ch = curl_init($api_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($post_data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));

        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

        if ($http_code == 200) {
            $result_data = json_decode($response, true);
            if (isset($result_data['predicted_price'])) {
                $prediction_result = $result_data['predicted_price'];
            } else if (isset($result_data['error'])) {
                $error_message = "Prediction error: " . htmlspecialchars($result_data['error']);
            } else {
                $error_message = "Failed to get prediction from the API.";
            }
        } else {
            $error_message = "Error connecting to the prediction API (HTTP status: " . $http_code . ")";
        }

        curl_close($ch);
    } else {
        $error_message = "Please select a product and a prediction date.";
    }
}

// Close database connection
$conn->close();
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



