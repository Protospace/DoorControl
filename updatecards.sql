select 'Start: ' ||  max(id) || ' Max, ' from cards;
select count(id) || ' Active...   ' from cards where active = 1;
drop table card2;
drop table card_backup;
CREATE TABLE card2 (serial varchar(255),active INTEGER, id INTEGER,last_seen varchar(255), first_seen varchar(255), owner varchar(255), notes varchar(255), soundbyte varchar(255), member_id INTEGER);
.import CardExport.txt card2
create table card_backup as select * from cards;
delete from cards;
INSERT INTO  cards   (serial,active,owner,last_seen, first_seen , owner , notes , soundbyte , member_id ) select serial,active,owner,last_seen,first_seen,owner,notes,soundbyte,member_id from card2;
update cards set first_seen=(select first_seen from card_backup cb where serial=cards.serial), last_seen = (select last_seen from card_backup where serial=cards.serial);
select 'End: ' ||  max(id) || ' Max, ' from cards;
select count(id) || ' Active. ' from cards where active = 1;


