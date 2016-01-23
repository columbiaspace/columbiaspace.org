# The website of the Columbia Space Initiative

This project is being continued from https://github.com/prichardsf/ColumbiaSpace .

## How to use GitHub

1. Make an account on GitHub.
2. Download the desktop client at desktop.github.com
3. Clone our CSI repo at https://github.com/columbiaspace/columbiaspace.github.io 
	1. This will download our files to your computer.
	2. You can make changes to these files, and then those changes will show up on the GitHub desktop client.
4. To push changes to our master branch, simply click "Commit to Master" on the GitHub desktop client and then press "sync" on the top right.

Note that you must be added as a contributer to this repo.

## Website specs

The website was initially designed with bootstrap, and later templated through jekyll. Focus was placed at providing clean content on all devices through responsive design and simplifying updating the website through templating.

The mission pages of the website are completely templated to allow for non-developers to update the website. Most elements are scalable to require the least amount of maintenance as possible.

The calendar implements the FullCalendar plugin, and the email signup is powered by mailchimp.

## How to make posts!

1. Log in to your GitHub account.
2. Create a new file under the folder "_posts"
3. Name the file with the following: year-month-date-subsection-title.markdown (e.g. "2015-11-13-micro-g-update.markdown")
	1. Note that this is a markdown file. You can read about formatting markdown files [here](https://help.github.com/articles/markdown-basics/) if you want fancier formatting for your post.
4. The template for your file should be the following, and then just push your post when you're done!

```
---
layout: post
title:  "Micro-G Update"
date:   2016-11-13
categories: microg
---
Text goes here.

-Sign it here!
```

## Contributors

@jakehlee - Website design, content, Jekyll implementation

@leee - Jekyll migration/implementation

@prichards - Website design, content

