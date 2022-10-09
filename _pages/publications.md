---
layout: page
permalink: /publications/
title: publications
description:  111
abbrs: [MoA, SOUP, robo]
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
<div class="publications">

{%- for x in page.abbrs %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f papers -q @*[abbr={{x}}]* %}
{% endfor %}

</div>
