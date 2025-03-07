import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import minimize


def create_hist2d(x, y, weights, bins):  # bins[nx,ny]
    """Generates a 2d hist from input 1d axis for x,y. repeats them to match shape of weights X*Y (data points)
       x will be 0-100%
    """
    freqs = np.repeat(np.array([y], dtype=np.float64), len(x), axis=0)
    throts = np.repeat(np.array([x], dtype=np.float64), len(y), axis=0).transpose()
    throt_hist_avr, throt_scale_avr = np.histogram(x, 101, [0, 100])

    hist2d = np.histogram2d(throts.flatten(), freqs.flatten(),
                            range=[[0, 100], [y[0], y[-1]]],
                            bins=bins, weights=weights.flatten(), density=False)[0].transpose()

    hist2d = np.array(abs(hist2d), dtype=np.float64)
    hist2d_norm = np.copy(hist2d)
    hist2d_norm /= (throt_hist_avr + 1e-9)

    return {'hist2d_norm': hist2d_norm, 'hist2d': hist2d, 'throt_hist': throt_hist_avr,
            'throt_scale': throt_scale_avr}


def spectrum(time, traces):
    """Fouriertransform for noise analysis. Returns frequencies and spectrum.
    """
    pad = 1024 - (len(traces[0]) % 1024)  # padding to power of 2, increases transform speed
    traces = np.pad(traces, [[0, 0], [0, pad]], mode='constant')
    trspec = np.fft.rfft(traces, axis=-1, norm='ortho')
    trfreq = np.fft.rfftfreq(len(traces[0]), time[1] - time[0])
    return trfreq, trspec


def equalize(time, data):
    """Equalizes time scale
    """
    data_f = interp1d(time, data)
    newtime = np.linspace(time[0], time[-1], len(time), dtype=np.float64)
    return newtime, data_f(newtime)


def stepcalc(time, duration):
    """Calculates frequency and resulting windowlength
    """
    tstep = (time[1] - time[0])
    freq = 1. / tstep
    arr_len = duration * freq
    return int(arr_len)


def weighted_avg_and_std(values, weights) -> tuple:
    """Calculates weighted avverage and resulting errors
    """
    average = np.average(values, axis=0, weights=weights)
    variance = np.average((values - average) ** 2, axis=0, weights=weights)
    return average, np.sqrt(variance)


def tukeywin(num: int, alpha: float = 0.5) -> np.ndarray:
    """Makes tukey widow for enveloping
    """
    if alpha <= 0:
        return np.ones(num)  # rectangular window
    elif alpha >= 1:
        return np.hanning(num)
    # Normal case
    x = np.linspace(0, 1, num, dtype=np.float64)
    w = np.ones(x.shape)
    # first condition 0 <= x < alpha/2
    first_condition = x < alpha / 2
    w[first_condition] = 0.5 * (1 + np.cos(2 * np.pi / alpha * (x[first_condition] - alpha / 2)))
    # second condition already taken care of
    # third condition 1 - alpha / 2 <= x <= 1
    third_condition = x >= (1 - alpha / 2)
    w[third_condition] = 0.5 * (1 + np.cos(2 * np.pi / alpha * (x[third_condition] - 1 + alpha / 2)))
    return w


def calc_delay(time, trace1, trace2):
    """Minimizes trace1-trace2 by shifting trace1
    """
    tf1 = interp1d(time[2000:-2000], trace1[2000:-2000], fill_value=0., bounds_error=False)
    tf2 = interp1d(time[2000:-2000], trace2[2000:-2000], fill_value=0., bounds_error=False)
    fun = lambda x: ((tf1(time - x * 0.5) - tf2(time + x * 0.5)) ** 2).mean()
    shift = minimize(fun, np.array([0.01])).x[0]
    steps = np.round(shift / (time[1] - time[0]))
    return {'time': shift, 'steps': int(steps)}


def rate_curve(rcin, inmax=500., outmax=800., rate=160.):
    # an estimated rate curve. not used.
    expoin = (np.exp((rcin - inmax) / rate) - np.exp((-rcin - inmax) / rate)) * outmax
    return expoin


def pid_in(pval, gyro, pidp):
    pidin = gyro + pval / (0.032029 * pidp)  # 0.032029 is P scaling factor from betaflight
    return pidin


def to_mask(clipped: np.ndarray) -> np.ndarray:
    clipped -= clipped.min()
    clipped /= clipped.max()
    return clipped


def stackspectrum(time, throttle, trace, window):
    # calculates spectrogram from stack of windows against throttle.
    # slicing off last 2s to get rid of landing
    gyro = trace[:-int(Trace.noise_superpos * 2. / Trace.noise_framelen), :] * window
    thr = throttle[:-int(Trace.noise_superpos * 2. / Trace.noise_framelen), :] * window
    time = time[:-int(Trace.noise_superpos * 2. / Trace.noise_framelen), :]

    freq, spec = spectrum(time[0], gyro)

    weights = abs(spec.real)
    avr_thr = np.abs(thr).max(axis=1)

    _hist2d = create_hist2d(avr_thr, freq, weights, [101, int(len(freq) / 4)])

    filt_width = 3  # width of gaussian smoothing for hist data
    hist2d_sm = gaussian_filter1d(_hist2d['hist2d_norm'], filt_width, axis=1, mode='constant')

    # get max value in histogram >100hz
    thresh = 100.
    mask = to_mask(freq[:-1:4].clip(thresh - 1e-9, thresh))
    maxval = np.max(hist2d_sm.transpose() * mask)

    return {'throt_hist_avr': _hist2d['throt_hist'], 'throt_axis': _hist2d['throt_scale'], 'freq_axis': freq[::4],
            'hist2d_norm': _hist2d['hist2d_norm'], 'hist2d_sm': hist2d_sm, 'hist2d': _hist2d['hist2d'], 'max': maxval}


def low_high_mask(signal, threshold):
    low = np.copy(signal)

    low[low <= threshold] = 1.
    low[low > threshold] = 0.
    high = -low + 1.

    if high.sum() < 10:  # ignore high pinput that is too short
        high *= 0.

    return low, high


class Trace:
    framelen = 10.  # length of each single frame over which to compute response
    resplen = 0.5  # length of respose window
    cutfreq = 25.  # cutfreqency of what is considered as input
    tuk_alpha = 1.0  # alpha of tukey window, if used
    superpos = 16  # sub windowing (superpos windows in framelen)
    threshold = 500.  # threshold for 'high input rate'
    noise_framelen = 0.3  # window width for noise analysis
    noise_superpos = 16  # subsampling for noise analysis windows

    def __init__(self, data):
        self.data = data
        self.input = equalize(data['time'], pid_in(data['p_err'], data['gyro'], data['P']))[1]  # /20.
        self.data.update({'input': pid_in(data['p_err'], data['gyro'], data['P'])})
        self.equalize_data()

        self.name = self.data['name']
        self.time = self.data['time']
        self.dt = self.time[0] - self.time[1]

        self.input = self.data['input']
        # enable this to generate artifical gyro trace with known system response
        # self.data['gyro']=self.toy_out(self.input, delay=0.01, mode='normal')##

        self.gyro = self.data['gyro']
        self.throttle = self.data['throttle']
        self.throt_hist, self.throt_scale = np.histogram(self.throttle, np.linspace(0, 100, 101, dtype=np.float64),
                                                         density=True)

        self.flen = stepcalc(self.time, Trace.framelen)  # array len corresponding to framelen in s
        self.rlen = stepcalc(self.time, Trace.resplen)  # array len corresponding to resplen in s
        self.time_resp = self.time[0:self.rlen] - self.time[0]

        self.stacks = self.winstacker({'time': [], 'input': [], 'gyro': [], 'throttle': []}, self.flen,
                                      Trace.superpos)  # [[time, input, output],]
        self.window = np.hanning(self.flen)  # self.tukeywin(self.flen, self.tuk_alpha)
        self.spec_sm, self.avr_t, self.avr_in, self.max_in, self.max_thr = self.stack_response(self.stacks, self.window)
        self.low_mask, self.high_mask = low_high_mask(self.max_in,
                                                      self.threshold)  # calcs masks for high and low inputs according to threshold
        self.toolow_mask = low_high_mask(self.max_in, 20)[1]  # mask for ignoring noisy low input

        self.resp_sm = self.weighted_mode_avr(self.spec_sm, self.toolow_mask, [-1.5, 3.5], 1000)
        self.resp_quality = -to_mask(
            (np.abs(self.spec_sm - self.resp_sm[0]).mean(axis=1)).clip(0.5 - 1e-9, 0.5)) + 1.
        # masking by setting trottle of unwanted traces to neg
        self.thr_response = create_hist2d(self.max_thr * (2. * (self.toolow_mask * self.resp_quality) - 1.),
                                          self.time_resp,
                                          (self.spec_sm.transpose() * self.toolow_mask).transpose(), [101, self.rlen - 1])

        self.resp_low = self.weighted_mode_avr(self.spec_sm, self.low_mask * self.toolow_mask, [-1.5, 3.5], 1000)
        if self.high_mask.sum() > 0:
            self.resp_high = self.weighted_mode_avr(self.spec_sm, self.high_mask * self.toolow_mask, [-1.5, 3.5], 1000)

        self.noise_winlen = stepcalc(self.time, Trace.noise_framelen)
        self.noise_stack = self.winstacker({'time': [], 'gyro': [], 'throttle': [], 'd_err': [], 'debug': []},
                                           self.noise_winlen, Trace.noise_superpos)
        self.noise_win = np.hanning(self.noise_winlen)

        self.noise_gyro = stackspectrum(self.noise_stack['time'], self.noise_stack['throttle'],
                                        self.noise_stack['gyro'], self.noise_win)
        self.noise_d = stackspectrum(self.noise_stack['time'], self.noise_stack['throttle'],
                                     self.noise_stack['d_err'], self.noise_win)
        self.noise_debug = stackspectrum(self.noise_stack['time'], self.noise_stack['throttle'],
                                         self.noise_stack['debug'], self.noise_win)
        if self.noise_debug['hist2d'].sum() > 0:
            # mask 0 entries
            thr_mask = self.noise_gyro['throt_hist_avr'].clip(0, 1)
            self.filter_trans = np.average(self.noise_gyro['hist2d'], axis=1, weights=thr_mask) / \
                                np.average(self.noise_debug['hist2d'], axis=1, weights=thr_mask)
        else:
            self.filter_trans = self.noise_gyro['hist2d'].mean(axis=1) * 0.

    def toy_out(self, inp, delay=0.01, length=0.01, noise=5., mode='normal', sinfreq=100.):
        # generates artificial output for benchmarking
        freq = 1. / (self.time[1] - self.time[0])
        toyresp = np.zeros(int((delay + length) * freq))
        toyresp[int(delay * freq):] = 1.
        toyresp /= toyresp.sum()
        toyout = np.convolve(inp, toyresp, mode='full')[:len(inp)]  # *0.9
        if mode == 'normal':
            noise_sig = (np.random.random_sample(len(toyout)) - 0.5) * noise
        elif mode == 'sin':
            noise_sig = (np.sin(2. * np.pi * self.time * sinfreq)) * noise
        else:
            noise_sig = 0.
        return toyout + noise_sig

    def equalize_data(self):
        # equalizes full dict of data
        time = self.data['time']
        newtime = np.linspace(time[0], time[-1], len(time), dtype=np.float64)
        for key in self.data:
            if isinstance(self.data[key], np.ndarray):
                if len(self.data[key]) == len(time):
                    self.data[key] = interp1d(time, self.data[key])(newtime)
        self.data['time'] = newtime

    def winstacker(self, stackdict, flen, superpos):
        # makes stack of windows for deconvolution
        tlen = len(self.data['time'])
        shift = int(flen / superpos)
        wins = int(tlen / shift) - superpos
        for i in np.arange(wins):
            for key in stackdict.keys():
                stackdict[key].append(self.data[key][i * shift:i * shift + flen])
        for k in stackdict.keys():
            # print 'key',k
            # print stackdict[k]
            stackdict[k] = np.array(stackdict[k], dtype=np.float64)
        return stackdict

    def wiener_deconvolution(self, vin, vout, cutfreq):  # vin/vout are two-dimensional
        pad = 1024 - (len(vin[0]) % 1024)  # padding to power of 2, increases transform speed
        vin = np.pad(vin, [[0, 0], [0, pad]], mode='constant')
        vout = np.pad(vout, [[0, 0], [0, pad]], mode='constant')
        H = np.fft.fft(vin, axis=-1)
        G = np.fft.fft(vout, axis=-1)
        freq = np.abs(np.fft.fftfreq(len(vin[0]), self.dt))
        sn = to_mask(np.clip(np.abs(freq), cutfreq - 1e-9, cutfreq))
        len_lpf = np.sum(np.ones_like(sn) - sn)
        sn = to_mask(gaussian_filter1d(sn, len_lpf / 6.))
        sn = 10. * (-sn + 1. + 1e-9)  # +1e-9 to prohibit 0/0 situations
        hcon = np.conj(H)
        deconvolved_sm = np.real(np.fft.ifft(G * hcon / (H * hcon + 1. / sn), axis=-1))
        return deconvolved_sm

    def stack_response(self, stacks, window):
        inp = stacks['input'] * window
        outp = stacks['gyro'] * window
        thr = stacks['throttle'] * window

        deconvolved_sm = self.wiener_deconvolution(inp, outp, self.cutfreq)[:, :self.rlen]
        delta_resp = deconvolved_sm.cumsum(axis=1)

        max_thr = np.abs(np.abs(thr)).max(axis=1)
        avr_in = np.abs(np.abs(inp)).mean(axis=1)
        max_in = np.max(np.abs(inp), axis=1)
        avr_t = stacks['time'].mean(axis=1)

        return delta_resp, avr_t, avr_in, max_in, max_thr

    def stackfilter(self, time, trace_ref, trace_filt, window):
        # calculates filter transmission and phaseshift from stack of windows. Not in use, maybe later.
        # slicing off last 2s to get rid of landing
        # maybe pass throttle for further analysis...
        filt = trace_filt[:-int(Trace.noise_superpos * 2. / Trace.noise_framelen), :] * window
        ref = trace_ref[:-int(Trace.noise_superpos * 2. / Trace.noise_framelen), :] * window
        time = time[:-int(Trace.noise_superpos * 2. / Trace.noise_framelen), :]

        full_freq_f, full_spec_f = spectrum(self.data['time'], [self.data['gyro']])
        full_freq_r, full_spec_r = spectrum(self.data['time'], [self.data['debug']])

        f_amp_freq, f_amp_hist = np.histogram(full_freq_f, weights=np.abs(full_spec_f.real).flatten(),
                                              bins=int(full_freq_f[-1]))
        r_amp_freq, r_amp_hist = np.histogram(full_freq_r, weights=np.abs(full_spec_r.real).flatten(),
                                              bins=int(full_freq_r[-1]))

    def weighted_mode_avr(self, values, weights, vertrange, vertbins):
        # finds the most common trace and std
        threshold = 0.5  # threshold for std calculation
        filt_width = 7  # width of gaussian smoothing for hist data

        resp_y = np.linspace(vertrange[0], vertrange[-1], vertbins, dtype=np.float64)
        times = np.repeat(np.array([self.time_resp], dtype=np.float64), len(values), axis=0)
        weights = np.repeat(weights, len(values[0]))

        hist2d = np.histogram2d(times.flatten(), values.flatten(),
                                range=[[self.time_resp[0], self.time_resp[-1]], vertrange],
                                bins=[len(times[0]), vertbins], weights=weights.flatten())[0].transpose()
        # shift outer edges by +-1e-5 (10us) bacause of dtype32. Otherwise different precisions lead to artefacting.
        # solution to this --> somethings strage here. In outer most edges some bins are doubled, some are empty.
        # Hence sometimes produces "divide by 0 error" in "/=" operation.

        if hist2d.sum():
            hist_sm = gaussian_filter1d(hist2d, filt_width, axis=0, mode='constant')
            hist_sm /= np.max(hist_sm, 0)
            pixelpos = np.repeat(resp_y.reshape(len(resp_y), 1), len(times[0]), axis=1)
            avr = np.average(pixelpos, 0, weights=pow(hist_sm, 2))
        else:
            hist_sm = hist2d
            avr = np.zeros_like(self.time_resp)
        # only used for monochrome error width
        hist2d[hist2d <= threshold] = 0.
        hist2d[hist2d > threshold] = 0.5 / (vertbins / (vertrange[-1] - vertrange[0]))

        std = np.sum(hist2d, 0)

        return avr, std, [self.time_resp, resp_y, hist_sm]
