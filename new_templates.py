import json
import sys
import collections
import warnings
import copy
import pickle

import numpy as np
from tqdm.auto import tqdm

import hist
import uproot
# with warnings.catch_warnings():
#     warnings.simplefilter("ignore")
#     import uproot
    # from uproot3_methods.classes.TH1 import Methods as TH1Methods
from coffea import processor
from coffea.util import load, save


def xSecReader(fname):
    # Probably unsafe
    with open(fname) as file:
        lines = file.readlines()
    lines = [l.strip("\n") for l in lines if not l.startswith("#")]
    lines = [l.split("#")[0] for l in lines if len(l) > 5]

    _dict = {}
    for line in lines:
        key = line.split()[0]
        valuex = line.split()[1:]
        if len(valuex) > 1:
            value = "".join(valuex)
        else:
            value = valuex[0]
        _dict[key] = float(eval(value))
    return _dict


def getSumW(accumulator):
    sumw = {}
    for key, accus in accumulator.items():
        sumw[key] = accus['sumw']
    return sumw


def scaleSumW(accumulator, sumw, lumi=1, xs={}):
    scaled = {}
    for sample, accu in accumulator.items():
        scaled[sample] = {}
        for key, h_obj in accu.items():
            if isinstance(h_obj, hist.Hist):
                h = copy.deepcopy(h_obj)
                if sample in xs.keys():
                    h = h * xs[sample]
                    h = h * 1000 / sumw[sample]  # * lumi - do later
                else:
                    if not (("JetHT" in sample) or ("SingleMuon" in key)):
                        warnings.warn(f"Sample ``{sample}`` cross-section not found. (MC won't be included).")
                scaled[sample][key] = h
    return scaled


def collate(accumulator, mergemap):
    out = {}
    for group, names in mergemap.items():
        out[group] = processor.accumulate([v for k, v in accumulator.items() if k in names])
    return out


def make_1dhist(h, cuts):
    return h[cuts]


def watcher(future_dict):
    import time
    with tqdm(total=len(future_dict), desc='Making templates') as pbar:
        while True:
            time.sleep(0.5)
            done = [future.done() for future in future_dict.values()]
            pbar.update(np.sum(done) - pbar.n)
            if all(done):
                break

    return {name: future.result() for name, future in future_dict.items()}


def make_1ds(collated,
             lumi,
             region='signal',
             kind='mu',
             noCvB=False,
             systs=True,
             dofutures=False,
             CvLcut=None,
             ptbinning='base'):
    assert kind in ['mu', 'signal']

    s = hist.tag.Slicer()
    proc_names = list(collated.keys())
    if "wqq" in proc_names:
        proc_names += ['wcq', 'zbb', 'zcc']
    BvLcut = 0.7
    if CvLcut is None:
        CvLcut = 0.45
    CvBcut = 0.03
    if CvLcut not in collated[list(collated.keys())[0]]['templates'].axes['ddc'].edges:
        raise ValueError(
            f"CvLcut = {CvLcut} not available. Axis edges are {collated[list(collated.keys())[0]]['templates'].axes['ddc'].edges}"
        )

    towrite = {}
    for proc in tqdm(proc_names, desc='Samples'):
        source_proc = proc
        if proc in ['wcq', 'wqq']:
            source_proc = 'wqq'
        if proc in ['zbb', 'zcc', 'zqq']:
            source_proc = 'zqq'

        try:
            h_obj = copy.deepcopy(collated[source_proc]['templates'])
        except:
            print(collated.keys())
            raise ValueError(f"{source_proc} not found")
        if proc not in ['data_obs', 'JetHT', 'SingleMuon']:
            h_obj = h_obj * lumi

        if kind == 'signal':
            if ptbinning == 'base':
                # binning = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
                binning = [(0, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
            elif ptbinning == 'splitfirst':
                binning = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
            elif ptbinning == 'raisefirst':
                binning = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
            else:
                raise ValueError(f"Unknown binning: {binning}")
        else:
            binning = [(0, 1)]
        # pt_iter = tqdm(h_obj.axes['pt'], desc='Bin', leave=False) if kind == 'signal' else [0]
        # for i, ptbin in enumerate(pt_iter):
        for i, bin_edges in enumerate(tqdm(binning, desc='Bin', leave=False)):
            for syst in tqdm(h_obj.axes['systematic'], desc='Syst', leave=False):
                if syst != "nominal" and proc == 'data_obs':
                    continue
                if not systs and syst != "nominal":
                    continue

                # Make slice dict
                cdict = {'systematic': syst, 'region': region}

                if kind == 'signal':
                    cdict['pt'] = s[bin_edges[0]:bin_edges[1]:sum]
                else:
                    cdict['pt'] = s[0:len:sum]
                if 'ddb' in h_obj.axes.name:
                    cdict['ddb'] = s[::sum]
                if 'runid' in h_obj.axes.name:
                    cdict['runid'] = s[::sum]
                if noCvB:
                    cdict['ddcvb'] = s[::sum]
                else:
                    cdict['ddcvb'] = s[hist.loc(CvBcut)::sum]

                # Add genflavor slices
                if proc in ['zbb', 'hbb']:
                    cdict['genflavor'] = s[3]
                elif proc == 'wcq' or proc in ['zcc', 'hcc']:
                    cdict['genflavor'] = s[2]
                elif proc == 'wqq' or proc == 'zqq':
                    cdict['genflavor'] = s[1]
                else:
                    cdict['genflavor'] = s[::sum]

                # Apply slices
                if dofutures:
                    pass_template = pool.submit(make_1dhist, h_obj, {**cdict, 'ddc': s[hist.loc(CvLcut)::sum]})
                    fail_template = pool.submit(make_1dhist, h_obj, {**cdict, 'ddc': s[:hist.loc(CvLcut):sum]})
                else:
                    try:
                        pass_template = h_obj[{**cdict, 'ddc': s[hist.loc(CvLcut)::sum]}]
                        fail_template = h_obj[{**cdict, 'ddc': s[:hist.loc(CvLcut):sum]}]
                    except:
                        pass_template = None
                        fail_template = None
                        print(f"Template for {proc} was empty.")

                    # if kind == 'mu' and source_proc == 'tqq':
                    #     print(pass_template)

                pass_name = f"{proc}_pass_{syst}"
                fail_name = f"{proc}_fail_{syst}"
                if kind == 'signal':
                    pass_name += f"_bin{i}"
                    fail_name += f"_bin{i}"

                towrite[pass_name] = pass_template
                towrite[fail_name] = fail_template
    return towrite


# class TH1(TH1Methods, list):
#     pass


# class TAxis(object):
#     def __init__(self, fNbins, fXmin, fXmax):
#         self._fNbins = fNbins
#         self._fXmin = fXmin
#         self._fXmax = fXmax


# def export1d(h_obj):
#     axis = h_obj.axes[0]
#     sumw, sumw2 = h_obj.values(flow=True), h_obj.variances(flow=True)
#     edges = h_obj.axes[0].edges

#     out = TH1.__new__(TH1)
#     out._fXaxis = TAxis(len(edges) - 1, edges[0], edges[-1])
#     out._fXaxis._fName = axis.name
#     out._fXaxis._fTitle = axis.label
#     out._fXaxis._fXbins = edges.astype(">f8")

#     centers = (edges[:-1] + edges[1:]) / 2.0
#     out._fEntries = out._fTsumw = out._fTsumw2 = sumw[1:-1].sum()
#     out._fTsumwx = (sumw[1:-1] * centers).sum()
#     out._fTsumwx2 = (sumw[1:-1] * centers ** 2).sum()

#     out._fName = "histogram"
#     out._fTitle = "Events"

#     out._classname = b"TH1D"
#     out.extend(sumw.astype(">f8"))
#     out._fSumw2 = sumw2.astype(">f8")

#     return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    parser.add_argument('--id', '--identifier', dest='identifier', default=r'', help='File identifier to carry through (default: %(default)s)')
    parser.add_argument("--year", default=2017, type=int, required=True, choices=[2016, 2017, 2018], help="Scale by appropriate lumi")
    parser.add_argument("-m", "--merge", "--mergemap", dest='mergemap', default=None, type=str, help="Load a mergemap json")
    parser.add_argument("--split", type=str2bool, default='True', choices={True, False}, help='Split W/Z by flavour')
    parser.add_argument("--muon", type=str2bool, default='True', choices={True, False}, help='Process muon templates')
    parser.add_argument("--systs", type=str2bool, default='False', choices={True, False}, help='Process systematics')
    # parser.add_argument("--futures", type=str2bool, default='False', choices={True, False}, help='Process systematics')
    parser.add_argument("-j", "--workers", default=0, type=int, help="Parallelize")
    # parser.add_argument("--type", default='cc', choices=['cc', 'bb', '3'], type=str, help="B templates or C tempaltes")
    parser.add_argument("--region", default='signal', choices=['signal', 'signal_noddt', 'signal_pure'], type=str, help="Which region in templates")
    parser.add_argument("--cvl", default=0.45, type=float, help="CvL cut")
    parser.add_argument("--ptbins", default='base', choices=['base', 'raisefirst', 'splitfirst'], type=str, help="pt binnings")
    parser.add_argument("-o", "--out", dest='output', default=None, type=str, help="Output file name eg `templates.root`")
    parser.add_argument("--dropB", type=str2bool, default='False', choices={True, False}, help='Dropped muon lumi')

    args = parser.parse_args()
    print("Running with the following options:")
    print(args)

    if args.year == 2017 and args.ptbins != 'raisefirst':
        print("Are you sure you don't want to raise low pT threshold in 2017?")
        user_input = input('Confirm? [Y/N]')
        if user_input.lower() not in ('y', 'yes'):
            sys.exit()
    elif args.year != 2017 and args.ptbins == 'raisefirst':
        print(f"Are you sure you want to raise low pT threshold in {args.year}?")
        user_input = input('Confirm? [Y/N]')
        if user_input.lower() not in ('y', 'yes'):
            sys.exit()

    lumi = {
        2016 : 36.33,
        2017 : 41.53,
        2018 : 59.74,
    }
    if args.dropB:
        lumi[2017] = 36.7
    lumi_mu = {
        2016 : 36.33,
        2017 : 41.53,
        2018 : 59.74,
    }

    file_kind = "CC"
    if args.output is None:
        template_file = f"templates_{args.identifier}_{file_kind}.root"
        template_mu_file = f"templatesmuCR_{args.identifier}_{file_kind}.root"
    else:
        _base_name = args.output.split(".root")[0]
        template_file = f"{_base_name}.root"
        template_mu_file = f"{_base_name}_mu.root"

    # Load info
    print(f'Processing coffea output from: hists_{args.identifier}.coffea')
    output = load(f'hists_{args.identifier}.coffea')

    xsecs = xSecReader('metadata/xSections_manual.dat')
    sumw = getSumW(output)

    if args.mergemap is not None:
        print(f'Processing with mergemap from: {args.mergemap}')
        with open(args.mergemap) as json_file:
            merge_map = json.load(json_file)
    else:
        merge_map = None

    if args.cvl not in output[list(output.keys())[0]]['templates'].axes['ddc'].edges:
        raise ValueError(
            f"args.cvl = {args.cvl} not available. Axis edges are {output[list(output.keys())[0]]['templates'].axes['ddc'].edges}"
        )

    # Scale and collate
    soutput = scaleSumW(output, sumw, xs=xsecs)
    collated = collate(soutput, merge_map)
    # Rename data
    collated['data_obs'] = collated['JetHT']

    # Make and write
    print(f'Will save templates to {template_file}')
    fout = uproot.recreate(template_file)
    print(f'Will save muon templates to {template_mu_file}')
    fout_mu = uproot.recreate(template_mu_file)

    if args.workers > 1:
        import concurrent
        pool = concurrent.futures.ProcessPoolExecutor(max_workers=args.workers)
    print(f'Making primary templates')
    _reg_map = {
            'signal': 'signal',
            'signal_noddt': 'signal_noddt',
            'signal_pure': 'signal_noddt',
        }
    template_dict = make_1ds(collated, lumi[args.year], region=_reg_map[args.region], kind='signal',
                             noCvB = True if 'pure' in args.region else False,
                             ptbinning=args.ptbins,
                             CvLcut=args.cvl,
                             systs=args.systs, dofutures=args.workers > 1)
    if args.workers > 1:
        template_dict = watcher(template_dict)
    for name, h_obj in tqdm(template_dict.items(), desc='Writing templates'):
        if h_obj is None:
            print(f'Template {name} is missing')
            continue
        if  np.sum(h_obj.values()) <= 0.:
            print(f'Template {name} is empty')
        if np.isnan(np.sum(h_obj.values())):
            print(f'Template {name} is nan')
        if len(h_obj.values()) != 23:
            print(h_obj.values())
            print(f'Template {name} has {len(h_obj.values())} bins')
        if name == 'qcd_fail_JERDown_bin5':
            print(h_obj.values())
            save(h_obj, 'h_obj.pkl')
        fout[name] = h_obj
    fout.close()

    if args.muon:
        print(f'Making muon CR templates')
        # Rename data
        collated['data_obs'] = collated['SingleMuon']
        # Make templates
        _muon_reg_map = {
            'signal': 'muoncontrol',
            'signal_noddt': 'muoncontrol_noddt',
            'signal_pure': 'muoncontrol_noddt',
        }
        template_dict = make_1ds(collated, lumi_mu[args.year], region=_muon_reg_map[args.region], kind='mu',
                                 noCvB=True if 'pure' in args.region else False,
                                 ptbinning=args.ptbins,
                                 systs=args.systs, dofutures=args.workers > 1)
        if args.workers > 1:
            template_dict = watcher(template_dict)
        for name, h_obj in tqdm(template_dict.items(), desc='Writing templates'):
            if h_obj is None:
                print(f'Template {name} is missing')
                continue
            if np.sum(h_obj.values()) <= 0.:
                print(f'Template {name} is empty')
            if np.isnan(np.sum(h_obj.values())):
                print(f'Template {name} is nan')
            fout_mu[name] = h_obj
        fout_mu.close()