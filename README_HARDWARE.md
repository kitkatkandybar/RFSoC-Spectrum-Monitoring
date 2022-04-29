# Hardware Overview

As for the hardware, we have not built any hardware. The hardware we have used for this project mainly consists of the RFSoC 2x2 board. In order to receive signals an antenna is also needed. Other RF accessories may be useful but the acquisition of them will strongly depend on the user’s needs.

## Schematics
<img width="452" alt="image" src="https://user-images.githubusercontent.com/72499097/165644857-6c7ba64d-688d-4a66-bba3-f66496dc6bd6.png">


From the previous Board Overview, the peripheral that we are using are:
- Both DACs and both ADCs
- USB3 peripheral
- Ethernet
- MicroSD
- Power rail

## Bill of Materials
It should be mentioned that the RFSoC 2x2 kit is exclusively for academic customers, the provider of the board is Xilinx. Link to purchase the board [here](https://www.xilinx.com/support/university/boards-portfolio/xup-boards/RFSoC2x2.html#Purchasing_at_academic_price).

Most of the remaining RF components were purchased from Minicircuits. Link to Minicrcuits webpage [here](https://www.minicircuits.com).

Below, a list of materials used for this project and its prices is provided (only the board and an antenna to monitor the RF spectrum is needed for basic monitoring):
| Item | Quantity | Description | Unit Cost | Extended Cost | 
| ----------- | ----------- | ----------- | ----------- | ----------- |
| 1      | 1       | Xilinx RFSoC 2x2 Kit      | $2149       |$2149       |
| 2      | 1       | Ethernet Cable      | $8        |$8        |
| 3      | 1       | SMA Cable      | $6        |$6        |
| 4      | 1       | OmniLOG PRO 1030 Antenna      | $270        |$270        |
| 5      | 2       | Mini-Circuits ZX60-P105LN+ Low Noise Amplifier      | $90        |$180        |
| 6      | 1       | Mini-Circuits VLF-1400+ LTCC Low Pass Filter      | $25        |$25        |
| 7      | 1       | Mini-Circuits FW-6+ 6 dB Fixed Attenuator      | $21        |$21        |
| 8      | 1       | Mini-Circuits VLM-33W-2W-S+ Limiter      | $50        |$50        |
| ||| Total cost        |$2709       |


## Important data sheets
For basic information about the hardware components and key futures of the RFSoC board refer to the [Xilinx webpage](https://www.xilinx.com/support/university/boards-portfolio/xup-boards/RFSoC2x2.html#hardware).

For more detailed information about the RFSoC board, including data sheets, board files and more, refer to the [dedicated project webpage](https://www.rfsoc-pynq.io).

We highly recommend using the previous webpage to familiarize with the board, it includes setup instructions, getting-started material, tutorials and much more useful content related to the board.


## Power requirements
In our project there are two components that require power:
- Board: requires 12V. The RFSoC board kit comes with a 12V-72W power supply unit.
- Low Noise Amplifier (LNA): requires 5V DC. To supply this voltage we use the DC POWER SUPPLY HY3005D. Some characteristics of this power supply:
    - It can operate  in 115 AC or 230 AC
    - It has adjustable outputs: 0-30V and 0-5A 

## Board setup

Since the RFSoC has two channels (each with one transmitter and one receiver), in this example we are connecting:
- In channel 0: an antenna to ADC2 (receiver), to monitor the RF spectrum.
- In channel 1: with an SMA cable, DAC1 (transmitter) and ADC1 (receiver), loopback mode, for testing purposes. It allows us to control exactly what data goes into the receiver, so that we can easily test whether or not the data being displayed on our application is accurate. 

<img width="600" alt="image" src="https://user-images.githubusercontent.com/72499097/165651782-dc2c7033-809b-4d4d-aa2b-1812bb7753b3.png">

1. SMA cable: This cable connects, for the same channel, the transmitter (DAC) to the receiver (ADC), loopback. 
2. Basic SDR antenna.
3. Power cable.
4. Ethernet cable: This cable connects the board to the internet. It can be connected to a router or to a PC with internet access.
5. Micro USB cable: This cable connects the board to the PC which we use to control the board. Specifically, the PC accesses JupyterLab on the RFSoC, which allows us to run Python scripts on the board. 


In the following example we have the same set up as in the previous example but we have added some RF components connected between the antenna and the input of ADC2.

<img width="600" alt="image" src="https://user-images.githubusercontent.com/72499097/165775462-99731f6a-8846-4319-baea-4b550b367b94.png">

The RF components present for this set up are:
1. Basic SDR Antenna
2. Low Pass Filter: passes signals with a frequency lower than its cutoff frequency, in this case 1400MHz
3. Low Noise Amplifier: amplifies a very low-power signal
4. Limiter: prevents damage to the LNA due to excessive power at the input of the system

Note: In the image, the LNA is not connected to the power supply, it should be connected for the LNA to work on the circuit.

For information about these components visit the [Minicircuits webpage](https://www.minicircuits.com) and search for the specific component (the full name of each component is provided in [Bill of Materials](#Bill-of-Materials)). Datasheets and more detailed information is provided there.
