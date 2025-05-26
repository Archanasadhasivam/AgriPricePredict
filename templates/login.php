<?php
// Start session and connect to database
session_start();
include 'db_connect.php'; // This file should create $conn = new mysqli(...);

if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_POST['ajax'])) {
    // Send response as JSON
    header('Content-Type: application/json');
    $response = [];

    // Get input values
    $email = trim($_POST['email']);
    $password = trim($_POST['password']);

    if (empty($email) || empty($password)) {
        $response['status'] = 'error';
        $response['message'] = 'Email and Password are required!';
    } else {
        // Prepare and execute query
        $stmt = $conn->prepare("SELECT id, email, password FROM users WHERE email = ?");
        $stmt->bind_param("s", $email);
        $stmt->execute();
        $result = $stmt->get_result();

        if ($result->num_rows === 1) {
            $row = $result->fetch_assoc();

            // Verify hashed password
            if (password_verify($password, $row['password'])) {
                $_SESSION['user_email'] = $row['email'];
                $_SESSION['user_id'] = $row['id'];

                $response['status'] = 'success';
                $response['redirect'] = 'dashboard.php';
            } else {
                $response['status'] = 'error';
                $response['message'] = 'Incorrect password!';
            }
        } else {
            $response['status'] = 'error';
            $response['message'] = 'User not found!';
        }

        $stmt->close();
    }

    $conn->close();
    echo json_encode($response);
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login</title>
    <style>
        body {
    font-family: Arial, sans-serif;
    background: #f4f4f4;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh; /* This is key for centering vertically */
    margin: 0;
}

.login-container {
    background: #fff;
    padding: 30px;
    border-radius: 10px;
    box-shadow: 0 0 15px rgba(0,0,0,0.1);
    width: 350px;
    text-align: center;
}

        h2 {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin: 10px 0 5px;
            text-align: left;
        }

        input[type="email"],
        input[type="password"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 6px;
            box-sizing: border-box;
        }

        button {
            width: 100%;
            padding: 10px;
            margin-top: 20px;
            background-color: #3dd5f3;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            background-color: #26c0dd;
        }

        #message {
            margin-top: 10px;
            color: red;
        }

        .signup-link {
            margin-top: 15px;
            font-size: 14px;
        }

        .signup-link a {
            color: #007bff;
            text-decoration: none;
        }

        .signup-link a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<div class="login-container">
    <h2>Login</h2>
    <p id="message"></p>
    <form id="loginForm" onsubmit="return false;">
        <label>Email:</label>
        <input type="email" name="email" required>

        <label>Password:</label>
        <input type="password" name="password" required>

        <button type="submit">Login</button>
    </form>

    <div class="signup-link">
        Don't have an account? <a href="signup.php">Sign up here</a>.
    </div>
    <div class="signup-link">
        Are you an admin? <a href="admin_login.php">Click here to login as admin</a>.
    </div>
</div>

<script>
    const form = document.getElementById('loginForm');
    const message = document.getElementById('message');

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = new FormData(form);
        formData.append('ajax', '1');

        fetch('login.php', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                window.location.href = data.redirect;
            } else {
                message.textContent = '❌ ' + data.message;
            }
        })
        .catch(error => {
            message.textContent = '❌ Something went wrong!';
            console.error(error);
        });
    });
</script>

</body>
</html>

