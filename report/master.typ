#import "template/report/lib.typ": *

#show: body => report(
  title: [CS 768 Assignment],
  authors: (
    (
      name: "Aditya Singh",
      email: "22b0056@iitb.ac.in"
    ),
  ),
  body
)

#show heading: it => {
  let number = if it.numbering != none {
    context {
      counter(heading).display(it.numbering)
    }
  }
  if it.numbering != none {
    [Task #number: #it.body]
  } else {
    [#it.body]
  }
}

The code for this assignment is available at #url("https://github.com/adityasz/cs768-assignment").
Detailed instructions for setup and running the scripts, as well as reproducing
all the results including this report (with all the figures and tables), are
available in the #link("https://github.com/adityasz/cs768-assignment/tree/master/README.md")[`README`].

#include "task1.typ"
#include "task2.typ"

#bibliography("refs.bib")
