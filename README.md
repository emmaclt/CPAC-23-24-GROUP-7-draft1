# χαρμολύπη (Charmolypi)
### Abstract
***χαρμολύπη*** is an interactive artistic experience aiming to explore the *beauty of closeness* in the context of human relationships. 

The loss of social connection often leads to feeling lonely and pained. Relationships are the expression of the choice to risk start losing something personal in exchange for making space for something enriching. 

Distance is hereby understood as solitude: individuals are self-contained beings when apart but when they choose to start getting closer to one another, an exchange gradually happens. This exchange will inevitably translate into the opening of their respective boundaries, sharing parts of themselves to receive something valuable in exchange. 

The intention behind this project is to explore and abractly represent what humans possess and can choose to share of themselves, enhancing the value of the enriching effect closeness in relationships has on the individual. 

The **final purpose** of the installation is for the user to perceive *human connection* as something *empowering* and *valuable* and to highlight the joy that comes from choosing to transition from solitude to community. Closeness, sharing and openness are all choices that the installation wants to promote and encourage. 

##  
Final project for the '_Creative Programming and Computing_' course of MSc. in _Music and Acoustic Engineering @ Politecnico di Milano_ (a.y. 2023/2024) held by [Prof. Massimiliano Zanoni](http://www.massimilianozanoni.it). 

Developed by:

- [Emma Coletta](https://github.com/emmaclt)
- [Enrico Dalla Mora](https://github.com/EnricoDallaMora)
- [Federico Ferreri](https://github.com/federicoalferreri)
- [Lorenzo Previati](https://github.com/LorenzoPreviati22)

## Links
- [Project Proposal Presentation]()
- [Final Project Presentation]()
- [📄Report]()
- [🎞️Video Demo]()

## Flowchart and Technical Summary

<img width="1440" alt="flowchart" src="https://github.com/emmaclt/CPAC-23-24-GROUP-7-draft1/assets/115798271/20c40775-68e2-4a11-92a1-da18a91f88d8">

### Hardware and Software Implementation

Our testing development setup involved:
- [Xbox Kinect Technology](https://en.wikipedia.org/wiki/Kinect)
  - motion detection 
- [TouchDesigner by Derivative.ca](https://derivative.ca)
  - motion mapping
  - visual and graphics
- [Python](https://www.python.org/downloads/)
  - variable markov chain algorithm implementation
  - music sequence generation and composition
- [SuperCollider software](https://supercollider.github.io)
  - sound synthesis
- [Open Sound Control](https://opensoundcontrol.stanford.edu/index.html)
  - networking and communication protocol

### External Resources
- [MAESTRO-v3.0.0 dataset](https://magenta.tensorflow.org/datasets/maestro#v300) [^1] by [Magenta](https://github.com/magenta/magenta)
  - midi files used to generate music sequences
<!--- [Markov Chain?]()-->

### Dependencies 
- Python
  - [Mido - MIDI Objects for Python](https://github.com/mido/mido)
  - [pyOSC3](https://github.com/Qirky/pyOSC3.git)

## Run on your machine

### Requirements
- Hardware
  - Microsoft Kinect Xbox 360
- Software:
  - [TouchDesigner](https://derivative.ca)
  - [Python](https://www.python.org/downloads/)
  - [SuperCollider](https://supercollider.github.io)
  – Python Dependencies

### How to
1. Make sure you have all software requirements mentioned above installed
2. Set up your hardware and software (TouchDesigner) communication
3. Execute the first ... lines of [new.scd](./new.scd)
4. Run [play_enrico.py](./play_enrico.py)
5. Execute the rest of [new.scd](./new.scd)
6. Play with the installation moving around in space and obviously closing the distance between you and the other user(s). 




