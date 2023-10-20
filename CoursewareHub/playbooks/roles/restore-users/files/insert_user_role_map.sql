INSERT INTO user_role_map (user_id, role_id) 
  SELECT u.id AS user_id,r.id AS role_id FROM users u, roles r
  WHERE r.name = 'user';

INSERT INTO user_role_map (user_id, role_id)
  SELECT u.id as user_id,r.id as role_id FROM users u, roles r
  WHERE r.name = 'admin' AND u.admin;

