---
layout: page
permalink: /publications/
title: publications
description: 
abbrs: [MoA, SOUP, robo]
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
<div class="publications">

{%- for x in page.abbrs %}
  <h2 class="year"> :sparkles: </h2>
  {% bibliography -f papers -q @*[abbr={{x}}]* %}
{% endfor %}

</div>
