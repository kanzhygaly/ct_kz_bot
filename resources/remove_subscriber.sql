select * from users;

select u.user_id, u.name, u.surname from subscribers s inner join users u on s.user_id=u.user_id;

delete from subscribers where user_id=1003354638;