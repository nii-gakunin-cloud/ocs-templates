SELECT l.mail FROM local_users l LEFT JOIN users u
  ON l.user_name = u.name WHERE u.admin;
