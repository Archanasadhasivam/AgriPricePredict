<?php
$conn = new mysqli("localhost", "root", "", "price_prediction");

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>

