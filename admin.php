<?php
// Start session
session_start();

// DB connection
$host = "localhost";
$user = "root";
$password = "";
$dbname = "price_prediction";

$conn = new mysqli($host, $user, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Handle delete request
if (isset($_GET['delete_id'])) {
    $deleteId = intval($_GET['delete_id']);
    $deleteQuery = "DELETE FROM users WHERE id = $deleteId";
    $conn->query($deleteQuery);
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