<?php
session_start();

// Corrected session variable to match login.php
if (!isset($_SESSION['user_email'])) {
    header("Location: login.php"); // Redirect to login if not logged in
    exit();
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f8f9fa;">

    <nav style="background-color: #53cadf; padding: 15px; color: white; text-align: center;">
        <h2 style="margin: 0;">User Dashboard</h2>
    </nav>

    <div style="max-width: 800px; margin: 30px auto; padding: 20px; background: white;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); border-radius: 10px; text-align: center;">

        <h3>Welcome, <?php echo htmlspecialchars($_SESSION['user_email']); ?>!</h3>

        <p>This web application helps farmers, traders, and policymakers track market prices of agricultural and horticultural commodities like pulses and vegetables. It provides insights based on seasonality, production estimates, and past trends. The goal is to support better planning and help stabilize market fluctuations.</p>

        <div style="margin-top: 20px;">
            <a href="alert_setting.php" style="text-decoration: none; padding: 10px 20px; background-color: #28a745; color: white; border-radius: 5px; margin: 5px;">Set Alert</a>
            <a href="predict_price.php" style="text-decoration: none; padding: 10px 20px; background-color: #ffc107; color: white; border-radius: 5px; margin: 5px;">Predict Price</a>
            <a href="historical_price.php" style="text-decoration: none; padding: 10px 20px; background-color: #17a2b8; color: white; border-radius: 5px; margin: 5px;">View Price Trend</a>
            <a href="logout.php" style="text-decoration: none; padding: 10px 20px; background-color: #dc3545; color: white; border-radius: 5px; margin: 5px;">Logout</a>

        </div>
    </div>

</body>
</html>
