<?php
// Start session
session_start();

// DB connection - Use the Aiven connection details
$host = "mysql-fc0e3b0-sadhasivamkanaga15-f154.l.aivencloud.com";
$port = 21436;
$user = "avnadmin";
$password = "AVNS_P2X1P7jH__WuLtv9YSs"; // IMPORTANT: Replace with your actual Aiven password!
$dbname = "defaultdb";

$conn = new mysqli($host, $user, $password, $dbname, $port);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Handle delete request
if (isset($_GET['delete_id'])) {
    $deleteId = intval($_GET['delete_id']);
    $deleteQuery = "DELETE FROM users WHERE id = ?";
    $stmt = $conn->prepare($deleteQuery);
    $stmt->bind_param("i", $deleteId);
    $stmt->execute();

    if ($stmt->affected_rows > 0) {
        // Optionally, set a success message
        $_SESSION['message'] = "User deleted successfully.";
        $_SESSION['message_type'] = 'success';
    } else {
        // Optionally, set an error message
        $_SESSION['message'] = "Error deleting user.";
        $_SESSION['message_type'] = 'danger';
    }
    $stmt->close();
    header("Location: admin_dashboard.php"); // Redirect back to the admin dashboard
    exit();
}

// Fetch all users
$userQuery = "SELECT id, username, email FROM users";
$result = $conn->query($userQuery);
?>

<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            background: #f2f2f2;
        }

        h2 {
            text-align: center;
        }

        .logout-btn {
            display: inline-block;
            background-color: #e60000;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            font-weight: bold;
            border-radius: 5px;
            position: absolute;
            top: 20px;
            right: 20px;
        }

        .logout-btn:hover {
            background-color: #cc0000;
        }

        table {
            border-collapse: collapse;
            width: 80%;
            margin: 60px auto 20px auto;
            background: #fff;
        }

        th, td {
            border: 1px solid #ccc;
            padding: 10px;
            text-align: center;
        }

        th {
            background-color: #4CAF50;
            color: white;
        }

        a.delete-btn {
            color: red;
            text-decoration: none;
        }

        a.delete-btn:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<a class="logout-btn" href="logout.php">Logout</a>

<h2>Admin Dashboard - User Management</h2>

<table>
    <tr>
        <th>ID</th>
        <th>Username</th>
        <th>Email</th>
        <th>Action</th>
    </tr>
    <?php if ($result && $result->num_rows > 0): ?>
        <?php while($row = $result->fetch_assoc()): ?>
        <tr>
            <td><?= htmlspecialchars($row['id']) ?></td>
            <td><?= htmlspecialchars($row['username']) ?></td>
            <td><?= htmlspecialchars($row['email']) ?></td>
            <td>
                <a class="delete-btn" href="admin.php?delete_id=<?= $row['id'] ?>" onclick="return confirm('Are you sure to delete this user?')">Delete</a>
            </td>
        </tr>
        <?php endwhile; ?>
    <?php else: ?>
        <tr><td colspan="4">No users found.</td></tr>
    <?php endif; ?>
</table>

</body>
</html>

<?php $conn->close(); ?>
