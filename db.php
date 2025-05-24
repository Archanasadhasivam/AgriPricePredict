<?php
$servername = "localhost";
$username = "root"; // Default for XAMPP
$password = ""; // Default is empty for XAMPP
$database = "price_prediction";

$conn = new mysqli($servername, $username, $password, $database);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>