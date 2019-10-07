# Context-Aware

This codes addresses a simple implementation of 5G NR to simulate the initial access procedure under information context

## The Code
The code includes the frame structure of 5G NR and has the following dependencies:
* python 3
* Numpy and Scipy
* Simpy

The C++ code is used to calculate the SNR given some parameters, already defined. It is necessary to compile the file (with `g++ -std=c++11 -o initial-access ia.cpp`, for example) to successfuly run the python script.

######Inputs

The python code waits for some inputs. Theses inputs are respectively: the IA algorithm, the channel condition, the average GPS error and the pseudo random number generator seed. For instance:

```
python3 newradio.py 0 1 10 1
```
means that the code will run with exaustive algorithm (0), LoS condition (1), 10 m of average GPS error and seed 1.

## Reference

If you use any data or code, please cite.

## License
