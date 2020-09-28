select *
from users;

select u.user_id, u.name, u.surname
from subscribers s
         inner join users u on s.user_id = u.user_id;

delete
from subscribers
where user_id = 1003354638;

-- delete duplicates
DELETE
FROM subscribers a USING subscribers b
WHERE a.id < b.id
  AND a.user_id = b.user_id;