<?php
$hostname = "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com";
$port = 21436;
$username = "avnadmin";
$password = "AVNS_P2X1P7jH_WuLtv9YSs"; // IMPORTANT: Replace "YOUR_AVION_PASSWORD" with your actual Aiven password!
$database = "defaultdb";

$conn = new mysqli($hostname, $username, $password, $database, $port);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>

