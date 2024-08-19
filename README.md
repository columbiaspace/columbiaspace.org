<img style="float: right;" src="https://columbiaspace.org/assets/media/img/csi-logo-small.png">

## How to use GitHub

1. Make an account on GitHub.
2. Download the desktop client at [desktop.github.com](https://desktop.github.com)
3. Clone our CSI repo at https://github.com/columbiaspace/columbiaspace.github.io
	1. This will download our files to your computer.
	2. You can make changes to these files, and then those changes will show up on the GitHub desktop client.
4. To push changes to our master branch, simply click "Commit to Master" on the GitHub desktop client and then press "sync" on the top right.

Note that you must be added as a contributer to this repo.

## Website specs

The website was initially designed with bootstrap, and later templated through jekyll. Focus was placed at providing clean content on all devices through responsive design and simplifying updating the website through templating.

The mission pages of the website are completely templated to allow for non-developers to update the website. Most elements are scalable to require the least amount of maintenance as possible.

The calendar implements the FullCalendar plugin, and the email signup is powered by mailchimp.

## Getting started

1. Make sure you have cloned the repo (see **How to use GitHub** above). Navigate to the local repo in terminal.

2. [Download and install Ruby](https://www.ruby-lang.org/en/downloads/). I recommend using [rbenv](https://github.com/rbenv/rbenv), because it makes everything else easier.

3. Confirm Ruby has been successfully installed by typing the following in terminal:

		ruby --version

4. Install [RubyGems](https://rubygems.org/), the Ruby package manager. Depending on how you installed Ruby, you might already have this installed. You can check if it has been installed by typing the following in terminal:

		gem --version

5. Make sure you are in the repo directory in terminal before doing the following. Install Jekyll by typing the following in terminal:

		gem install bundler jekyll

6. Install the necessary packages by typing the following in terminal:

		bundle install

7. You're all done! You can now use jekyll to open the website on a local server. Type


		bundle exec jekyll serve

	in terminal and browse to `http://localhost:4000`. When the server boots up, you should see the columbiaspace.org website. Any changes you make to the source files will be automatically updated on this server.

If you need to update your packages according to the Gemfile, just run `bundle` (e.g. somebody else updates packages in the Gemfile and you need to get that same version, without messing with updating other packages).

## Troubleshooting Tips

*menu order is determined by the HTML file names within the corresponding folder

## How to make posts!

1. Log in to your GitHub account.
2. Create a new file under the folder "_posts"
3. Name the file with the following: `year-month-date-subsection-title.markdown` (e.g. `2015-11-13-micro-g-update.markdown`)
	1. Note that this is a markdown file. You can read about formatting markdown files [here](https://help.github.com/articles/markdown-basics/) if you want fancier formatting for your post.
	2. Also note that it must be `.markdown`, not `.mdown`
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

5. To imbed images in your posts, use this!

```
<p align="center">
	<img src="/assets/media/img/specifypathhere.jpg" alt="a quick work or two" />
</p>
```

## Contributors

Gregory Schare ([@gschare](https://github.com/gschare)) - Webmaster

Jake Lee ([@jakehlee](https://github.com/jakehlee)) - Website design, content, Jekyll implementation

Emma Lee ([@leee](https://github.com/leee)) - Jekyll migration/implementation

Peter Richards ([@pr](https://github.com/pr)) - Website design, content, Jekyll implementation

Lily He ([@tigerlily-he](https://github.com/tigerlily-he)) - content

Theodore Nelson ([@Theo-Nelson](https://github.com/Theo-Nelson)) - content

Jacob Boxerman ([@jakebox](https://github.com/jakebox)) - Webmaster 2023-24
