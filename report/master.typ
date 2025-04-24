#import "@templates/report:0.1.0": *


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
