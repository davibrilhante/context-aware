import simutime as st

'''
Global definitions
'''
SSBLOCK_LENGTH = 4 #in OFDM Symbols
FRAME_DURATION = st.milliseconds(10).micro()
SUBFRAME_DURATION = st.milliseconds(1).micro()
BURST_DURATION = st.milliseconds(5).micro()
BURST_PERIOD = st.milliseconds(20).micro()
RACH_PERIOD = st.milliseconds(80).micro()
SIM_DURATION = st.seconds(10).micro()
LTE_RTT = st.milliseconds(1).micro()
ENV_RADIUS = 100 #meters
RATIO = RACH_PERIOD/BURST_PERIOD # 1 RACH and (RATIO-1) Burst Set
