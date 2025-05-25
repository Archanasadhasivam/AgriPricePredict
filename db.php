<?php
$host = "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com";
$port = 21436;
$user = "avnadmin";
$password = "AVNS_P2X1P7jH__WuLtv9YSs"; // IMPORTANT: Replace with your actual Aiven password!
$dbname = "defaultdb";

$conn = new mysqli($host, $user, $password, $dbname, $port);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
