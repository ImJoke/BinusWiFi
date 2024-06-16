<?php
// Function to get the client's IP address
function getClientIP() {
    $ip = 'UNKNOWN';
    $ip_keys = ['HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'];
    foreach ($ip_keys as $key) {
        if (isset($_SERVER[$key]) && filter_var($_SERVER[$key], FILTER_VALIDATE_IP)) {
            $ip = $_SERVER[$key];
            break;
        }
    }
    return $ip;
}

// Function to log IP address to PostgreSQL
function logIPToDatabase($ip) {
    // Retrieve database connection details from environment variables
    $dsn = getenv('POSTGRES_URL');
    $user = getenv('POSTGRES_USER');
    $password = getenv('POSTGRES_PASSWORD');

    try {
        $pdo = new PDO($dsn, $user, $password);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        // Ensure the table exists
        $sql = "CREATE TABLE IF NOT EXISTS criminal_ips (
            id SERIAL PRIMARY KEY,
            ip_address VARCHAR(45) NOT NULL,
            visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )";
        $pdo->exec($sql);

        // Insert the IP address
        $stmt = $pdo->prepare("INSERT INTO criminal_ips (ip_address, visit_time) VALUES (:ip_address, NOW())");
        $stmt->bindParam(':ip_address', $ip);
        $stmt->execute();
    } catch (PDOException $e) {
        error_log('Connection failed: ' . $e->getMessage());
        echo 'An error occurred while logging the IP address.';
    }
}

// Get the client's IP address
$ipAddress = getClientIP();

// Log the IP address to the database
logIPToDatabase($ipAddress);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Seized</title>
    <style>
        body {
            text-align: center;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-image: url('https://files.oaiusercontent.com/file-RzIU5Te1DIFytQCLIoN8vpZS?se=2024-06-16T02%3A57%3A55Z&sp=r&sv=2023-11-03&sr=b&rscc=max-age%3D31536000%2C%20immutable&rscd=attachment%3B%20filename%3D2f39fc30-0455-44f7-b0bf-7bd2baaf66b4.webp&sig=qNT7vPA4OrKyHwJaYwF0C9/eVjW/jOSZJf%2BXj2e3rRE%3D');
            background-size: cover;
            color: white;
        }
        .seized-message-container {
            background-color: rgba(0, 0, 0, 0.7);
            margin: 50px auto;
            padding: 20px;
            border-radius: 10px;
            width: 80%;
            max-width: 800px;
        }
        .seized-message-header {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .seized-message-body {
            font-size: 24px;
            margin-bottom: 20px;
        }
        .agency-logos {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
        .agency-logos img {
            height: 100px;
            margin: 0 20px;
        }
    </style>
</head>
<body>
    <div class="seized-message-container">
        <div class="seized-message-header">
            This website has been seized
        </div>
        <div class="seized-message-body">
            by BINUS University.
        </div>
        <div class="agency-logos">
            <img src="https://upload.wikimedia.org/wikipedia/id/a/a2/Logo_Binus_University.png" alt="BINUS Logo">
            <img src="https://media.licdn.com/dms/image/C510BAQFmIb2DuC7aFw/company-logo_200_200/0/1630613034687/it_binus_logo?e=2147483647&v=beta&t=ec74D4L8rK5Qt_Paw3oAb0zujgduL2Db0lJcoTKgUpE" alt="BINUS IT DIV Logo">
        </div>
        <div>
            As part of a joint law enforcement operation by
            <strong>BINUS University</strong>.
        </div>
    </div>
</body>
</html>
