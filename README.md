<!-- markdownlint-disable MD033 MD040 MD041 MD053 -->
<a name="readme-top"></a>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://www.uni-due.de/fmi/">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">SD-Simulate</h3>

  <p align="center">
    A simple way to view and simulate UML state diagrams
    <br />
    <a href="#About-The-Project">About the Project</a>
    ·
    <a href="#Getting-Started">Getting Started</a>
    ·
    <a href="#Usage">Usage</a>
  </p>
</div>



<!-- ABOUT THE PROJECT -->
<a name="About-The-Project"></a>
## About The Project

![Product Name Screen Shot][product-screenshot]

With this tool, you can display, execute and analyze UML state diagrams to get a better understanding of how transitions and regions interact with each other.
Supported analyses:
<br/>

* generate the corresponding reachability graph
* reachability analysis
* maxnode analysis to find a transition sequence covering as many states as possible
* maxtransition analysis to find the longest transition sequence possible

<br/>


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
<a name="Getting-Started"></a>
## Getting Started

### Prerequisites
In order to use this tool, you will need to install Python as well as Graphviz on your device.

* The latest version of Python can be found [here][python-url].
* The latest version of Graphviz can be found [here][graphviz-url].

### Installation
If you are having trouble installing the required Python3 Libraries see [here][python-help].

1. Clone the repository
   ```text
   git clone https://github.com/fmidue/sd-simulate
   ```
   or Download and save locally
2. Install [Cairosvg][cairosvg-package]
   ```text
  pip install cairosvg
   ```
3. Install [Graphviz-pylib][graphviz-package]
   ```text
   pip install graphviz
   ```
3. Install [Pycairo][pycairo-package]
   ```text
   pip install pycairo
   ```
4. Navigate to and [run][python-help2] main.py


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

<br/>
<strong>[Load UML Diagram]</strong> and navigate to the .svg or .txt file containing your graph <br>
<strong>[Show containment]</strong> to highlight the currently active region in red <br>
<strong>[Hint]</strong> to highlight the currently reachable states <br>
<strong>[Show State Diagram Graph]</strong> to generate the corresponding reachability graph<br>
<strong>[Reachability analysis]</strong> find all reachable states from the initial state <br>
<strong>[Max Node Analysis]</strong> find a transition sequence that contains as many states as possible <br>
<strong>[Max transition Analysis]</strong> to find a transition sequence that contains as many transitions as possible <br>
<a name="Usage"></a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
[python-url]: https://www.python.org/downloads/
[python-help]: https://packaging.python.org/en/latest/tutorials/installing-packages/
[python-help2]: https://pythonbasics.org/execute-python-scripts/
[graphviz-url]: https://graphviz.org/download/
[graphviz-package]: https://pypi.org/project/graphviz/
[cairosvg-package]: https://cairosvg.org/
[pycairo-package]: https://pypi.org/project/pycairo/

[product-screenshot]: images/screenshot.png
