select name, word_id, COUNT(word_index) as num_of_appearance
from word_appearance natural join word
group by word_id
order by COUNT(word_index) desc;