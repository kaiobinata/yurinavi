# https://www.mangaupdates.com/search.html?search=%E5%90%8C%E5%B1%85%E4%BA%BA%E3%81%8C%E4%B8%8D%E5%AE%89%E5%AE%9A%E3%81%A7%E3%81%97%E3%81%A6%281%E5%B7%BB%29
# The url text says: https://www.mangaupdates.com/search.html?search=同居人が不安定でして%281巻%29
# it's notable that ( is %28 and ) is %29
# in testing, I believe that this also works: https://www.mangaupdates.com/search.html?search=同居人が不安定でして(1巻)
# then obtain the first entry link under series: div class="col-6 py-1 py-md-0 text alt" -> <a>Title
