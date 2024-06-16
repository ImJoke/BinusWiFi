<?php
function getClientIP() {
    $ipaddress = '';
    if (isset($_SERVER['HTTP_CLIENT_IP']))
        $ipaddress = $_SERVER['HTTP_CLIENT_IP'];
    else if(isset($_SERVER['HTTP_X_FORWARDED_FOR']))
        $ipaddress = $_SERVER['HTTP_X_FORWARDED_FOR'];
    else if(isset($_SERVER['HTTP_X_FORWARDED']))
        $ipaddress = $_SERVER['HTTP_X_FORWARDED'];
    else if(isset($_SERVER['HTTP_FORWARDED_FOR']))
        $ipaddress = $_SERVER['HTTP_FORWARDED_FOR'];
    else if(isset($_SERVER['HTTP_FORWARDED']))
       $ipaddress = $_SERVER['HTTP_FORWARDED'];
    else if(isset($_SERVER['REMOTE_ADDR']))
        $ipaddress = $_SERVER['REMOTE_ADDR'];
    else
        $ipaddress = 'UNKNOWN';
    return $ipaddress;
}

function logIPToDatabase($ip) {
    // Retrieve database connection details from environment variables
    $host = getenv('POSTGRES_HOST');
    $port = "5432";
    $user = getenv('POSTGRES_USER');
    $password = getenv('POSTGRES_PASSWORD');
    $dbname = getenv('POSTGRES_DATABASE');
    $sslmode = "require";

    $dsn = "pgsql:host=$host;port=$port;dbname=$dbname;sslmode=$sslmode";

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
        echo 'An error occurred while logging the IP address: ' . $e->getMessage();
    }
}

logIPToDatabase(getClientIP());
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
            background-image: url('/assets/bg.webp');
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
