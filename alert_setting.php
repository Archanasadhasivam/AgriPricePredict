<?php
session_start();

if (!isset($_SESSION['user_email']) || !isset($_SESSION['user_id'])) {
    header("Location: login.php");
    exit();
}

include("db_connect.php"); // Ensure this uses your Aiven connection

$user_id = $_SESSION['user_id'];

// Handle alert deletion
if (isset($_GET['delete_id'])) {
    $delete_id = intval($_GET['delete_id']);
    $delStmt = $conn->prepare("DELETE FROM price_alerts WHERE id = ? AND user_id = ?");
    $delStmt->bind_param("ii", $delete_id, $user_id);
    $delStmt->execute();
    $delStmt->close();
    echo "<script>alert('Alert deleted successfully!'); window.location.href='/project/alert_setting.php';</script>";
    exit();
}

// Handle form submission for setting/updating alerts
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $product = $_POST['product'];
    $price = $_POST['price'];

    if (!empty($product) && !empty($price)) {
        $checkStmt = $conn->prepare("SELECT id FROM price_alerts WHERE user_id = ? AND product_name = ?");
        $checkStmt->bind_param("is", $user_id, $product);
        $checkStmt->execute();
        $checkStmt->store_result();

        if ($checkStmt->num_rows > 0) {
            $updateStmt = $conn->prepare("UPDATE price_alerts SET alert_price = ? WHERE user_id = ? AND product_name = ?");
            $updateStmt->bind_param("dis", $price, $user_id, $product);
            $updateStmt->execute();
            $updateStmt->close();
            echo "<script>alert('Alert updated successfully!');</script>";
        } else {
            $insertStmt = $conn->prepare("INSERT INTO price_alerts (user_id, product_name, alert_price) VALUES (?, ?, ?)");
            $insertStmt->bind_param("isd", $user_id, $product, $price);
            $insertStmt->execute();
            $insertStmt->close();
            echo "<script>alert('Alert set successfully!');</script>";
        }
        $checkStmt->close();
    } else {
        echo "<script>alert('Please fill in all fields!');</script>";
    }
}

// Fetch user's current alerts
$alerts = [];
$fetchStmt = $conn->prepare("SELECT id, product_name, alert_price FROM price_alerts WHERE user_id = ?");
$fetchStmt->bind_param("i", $user_id);
$fetchStmt->execute();
$result = $fetchStmt->get_result();
while ($row = $result->fetch_assoc()) {
    $alerts[] = $row;
}
$fetchStmt->close();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Price Alerts and Notifications</title>
</head>
<body style="display: flex; justify-content: center; align-items: center; min-height: 100vh; background-color: #f8f8f8;">
    <div style="background-color: white; padding: 20px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); width: 400px; text-align: center; border-radius: 10px;">
        <h2>Price Alerts and Notifications</h2>

        <form method="POST">
            <label for="product">Select Product:</label>
            <select id="product" name="product" style="width: 100%; padding: 5px; margin: 10px 0;" required>
                <?php
                $products = [
                    "onion", "potato", "tomato", "rice", "wheat", "atta (wheat)", "gram dal", "tur/arhar dal",
                    "urad dal", "moong dal", "masoor dal", "groundnut oil (packed)", "mustard oil (packed)",
                    "vanaspati (packed)", "soya oil (packed)", "sunflower oil (packed)", "palm oil (packed)",
                    "sugar", "gur", "milk", "tea loose", "salt pack (iodised)"
                ];
                foreach ($products as $prod) {
                    echo "<option value='" . htmlspecialchars($prod) . "'>" . htmlspecialchars(ucfirst($prod)) . "</option>";
                }
                ?>
            </select>

            <label for="price">Price Alert (₹/kg):</label>
            <input type="number" step="0.01" id="price" name="price" placeholder="Enter price threshold" style="width: 95%; padding: 5px; margin: 10px 0;" required>

            <button type="submit" style="width: 100%; padding: 10px; background-color: #53cadf; color: white; border: none; cursor: pointer;">Set Alert</button>
        </form>

        <?php if (!empty($alerts)) : ?>
            <h3 style="margin-top: 20px;">Your Alerts</h3>
            <table style="width: 100%; margin-top: 10px; border-collapse: collapse;">
                <tr style="background-color: #e0f7fa;">
                    <th style="padding: 8px;">Product</th>
                    <th style="padding: 8px;">Price</th>
                    <th style="padding: 8px;">Action</th>
                </tr>
                <?php foreach ($alerts as $alert) : ?>
                    <tr>
                        <td style="padding: 8px;"><?php echo htmlspecialchars($alert['product_name']); ?></td>
                        <td style="padding: 8px;">₹<?php echo number_format($alert['alert_price'], 2); ?></td>
                        <td style="padding: 8px;">
                            <a href="?delete_id=<?php echo $alert['id']; ?>" onclick="return confirm('Are you sure you want to delete this alert?');" style="color: blue;">Delete</a>
                        </td>
                    </tr>
                <?php endforeach; ?>
            </table>
        <?php endif; ?>

        <a href="dashboard.php" style="display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #53cadf; color: white; border-radius: 5px; text-decoration: none;">Back</a>
    </div>
</body>
</html>
