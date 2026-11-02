# Choose an Effective Visual — Sources

All pages were opened on 2026-11-01 and are listed in `docs/advisors/new_advisors/v_cole-nussbaumer-knaflic.md`.

## The method

The framework follows chapter 2 of *Storytelling with Data* (2015), "choosing an effective visual" ([Wiley table of contents PDF](https://media.wiley.com/product_data/excerpt/57/11190022/1119002257-6.pdf)), and Cole's post "SWD AI: choose an appropriate visual" ([blog](https://www.storytellingwithdata.com/blog/swd-ai-choose-an-appropriate-visual)), which maps bars to categories, lines to time, and dot plots and slopegraphs to change between two points.

## Phases

- **Phase 1, Who and What:** book chapter 1, who/what/how and exploratory vs. explanatory ([Wiley PDF](https://media.wiley.com/product_data/excerpt/57/11190022/1119002257-4.pdf)); "Your audience and takeaway should drive the choice" ([choose an appropriate visual](https://www.storytellingwithdata.com/blog/swd-ai-choose-an-appropriate-visual)).
- **Phase 2, Name the Comparison:** [choose an appropriate visual](https://www.storytellingwithdata.com/blog/swd-ai-choose-an-appropriate-visual). Part-to-whole as the pie's one use comes from Elizabeth Ricks, [how to make a better pie chart](https://www.storytellingwithdata.com/blog/2020/2/26/how-to-make-a-better-pie-chart).
- **Phase 3, Pick the Chart:** [choose an appropriate visual](https://www.storytellingwithdata.com/blog/swd-ai-choose-an-appropriate-visual); [when bars win—and when lines do](https://www.storytellingwithdata.com/blog/when-bars-winand-when-lines-do); Elizabeth Ricks, [visualizing change via slopegraph](https://www.storytellingwithdata.com/blog/2017/9/19/visualizing-change); Amy Esselman, [bar charts and dot plots and line graphs, oh my!](https://www.storytellingwithdata.com/blog/bar-charts-and-dot-plots-and-line-graphs-oh-my); Cole, [make a perfect pie](https://www.storytellingwithdata.com/blog/2020/8/2/swdchallenge-make-a-perfect-pie).
  - Added: the rule-outs for donut and 3D pies and for two pies side by side. They follow from Ricks's point that slices are hard to compare, but no source page states them this way.
- **Phase 4, The Rules for That Chart:** Alex Velez, [what is a bar chart?](https://www.storytellingwithdata.com/blog/2020/2/19/what-is-a-bar-chart) (zero baseline, sort by value, horizontal for long labels, gap thinner than the bar); Cole, [when bars win](https://www.storytellingwithdata.com/blog/when-bars-winand-when-lines-do) (lines must mean something); Amy Esselman, [oh my!](https://www.storytellingwithdata.com/blog/bar-charts-and-dot-plots-and-line-graphs-oh-my) (connected dot plot); Elizabeth Ricks, [better pie chart](https://www.storytellingwithdata.com/blog/2020/2/26/how-to-make-a-better-pie-chart) (direct labels, one colored slice, the "so what?").
  - Added: "a line graph's axis doesn't have to start at zero, because the eye reads the slope." This is standard charting practice, not taken from a source page.
  - Added: the dot-plot fix for a small difference the user wants a cut-off bar axis for. It follows from Velez's zero rule plus Esselman's dot plots; no page pairs them.
- **Phase 5, Too Many Lines or Too Many Bars:** Cole, [strategies for avoiding the spaghetti graph](https://www.storytellingwithdata.com/blog/2013/03/avoiding-spaghetti-graph) (panels with the same y-axis range; highlight one line at a time).
  - Added: "top five and an 'all others' bar" for too many bars. It follows Simon Rowe's point that a subset or total is often clearer than all the data ([when decluttering isn't enough](https://www.storytellingwithdata.com/blog/when-decluttering-isnt-enough)).
  - Added: panels for a live dashboard where the viewer picks the line. Reasoned from the two spaghetti fixes, not from a source page.
- **Phase 6, The Chart Decision:** Added. The one-page decision and the hand-offs to `declutter-and-focus` and `big-idea-and-takeaway-title` are the plugin's format for a decision framework.

## Cole's words used in the prompt and examples

- "Your audience and takeaway should drive the choice." and "Use something less familiar only when it reveals an insight that would otherwise be difficult to see." — [choose an appropriate visual](https://www.storytellingwithdata.com/blog/swd-ai-choose-an-appropriate-visual)
- "Bar charts are almost always a reasonable option." and "When opting for a line graph, you want the lines themselves to mean something." — [when bars win](https://www.storytellingwithdata.com/blog/when-bars-winand-when-lines-do)
- "Nearly every graph has a perfect use case—including the pie." and "The common condemnations of pie charts are mainly due to instances of poor use." — [make a perfect pie](https://www.storytellingwithdata.com/blog/2020/8/2/swdchallenge-make-a-perfect-pie)
- "It's important in the above example that my y-axis minimum and maximum are the same for each graph" — [spaghetti graph](https://www.storytellingwithdata.com/blog/2013/03/avoiding-spaghetti-graph)
- The "every rock you turned over" line in Phase 1 paraphrases her "turning over 100 rocks" picture ([exploratory vs. explanatory](https://www.storytellingwithdata.com/blog/2014/04/exploratory-vs-explanatory-analysis)). It is not quoted.

No story in `examples.md` is told as Cole's own. The support-team example is made up.

## Credit

- Alex Velez: bar chart rules.
- Elizabeth Ricks: slopegraphs; the better pie.
- Amy Esselman: dot plots.
- Simon Rowe: showing a subset instead of all the data.

Their practices are taught as storytelling with data practice and credited by name. None is quoted as Cole.
