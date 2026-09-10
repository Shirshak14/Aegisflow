"""
Dataset Adapters for CIC-IDS2018, CTU-13, UNSW-NB15, and Raw PCAP.
Normalizes diverse source formats into the standard canonical schema.
"""

import io
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Label mapping dictionaries from raw datasets to canonical MITRE stages
CIC_IDS_2018_LABEL_MAP = {
    "benign": "Normal",
    "ftp-bruteforce": "Initial Access",
    "ssh-bruteforce": "Initial Access",
    "dos attacks-goldeneye": "Execution",
    "dos attacks-slowloris": "Execution",
    "dos attacks-slowhttptest": "Execution",
    "dos attacks-hulk": "Execution",
    "brute force -web": "Initial Access",
    "brute force -xss": "Initial Access",
    "sql injection": "Initial Access",
    "infilteration": "Privilege Escalation",
    "bot": "Command and Control",
    "ddos attacks-loic-http": "Execution",
    "ddos attack-hoic": "Execution",
}

CTU_13_LABEL_MAP = {
    "normal": "Normal",
    "background": "Normal",
    "botnet": "Command and Control",
    "cc": "Command and Control",
    "c&c": "Command and Control",
    "scan": "Reconnaissance",
    "attack": "Execution"
}

UNSW_NB15_LABEL_MAP = {
    "normal": "Normal",
    "reconnaissance": "Reconnaissance",
    "fuzzers": "Reconnaissance",
    "analysis": "Reconnaissance",
    "backdoors": "Persistence",
    "dos": "Execution",
    "exploits": "Initial Access",
    "generic": "Execution",
    "worms": "Lateral Movement",
    "shellcode": "Execution"
}

class DatasetAdapter:
    """Normalizes raw tabular data (CSV/Parquet) into standard flow DataFrame."""

    @staticmethod
    def identify_format(df: pd.DataFrame) -> str:
        cols_lower = [c.lower().strip() for c in df.columns]
        if any("dst port" in c or "flow duration" in c or "tot fwd pkts" in c for c in cols_lower):
            return "CIC-IDS2018"
        elif any("dur" in c and "sbytes" in c and "attack_cat" in c for c in cols_lower):
            return "UNSW-NB15"
        elif any("srcaddr" in c or "dstaddr" in c or "totpkts" in c for c in cols_lower):
            return "CTU-13"
        return "GENERIC"

    @classmethod
    def adapt(cls, df: pd.DataFrame, dataset_type: Optional[str] = None) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        # Clean column names (strip spaces, lowercase)
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]

        if not dataset_type or dataset_type.upper() == "AUTO":
            dataset_type = cls.identify_format(df)

        if dataset_type.upper() == "CIC-IDS2018":
            return cls._adapt_cic_ids_2018(df)
        elif dataset_type.upper() == "UNSW-NB15":
            return cls._adapt_unsw_nb15(df)
        elif dataset_type.upper() == "CTU-13":
            return cls._adapt_ctu13(df)
        else:
            return cls._adapt_generic(df)

    @staticmethod
    def _adapt_cic_ids_2018(df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        # Mapping helpers
        col_map = {c.lower(): c for c in df.columns}
        
        # Timestamp
        ts_col = col_map.get("timestamp", col_map.get("time", None))
        if ts_col:
            out["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce").astype("int64") // 10**9
            out["timestamp"] = out["timestamp"].fillna(np.arange(len(df)))
        else:
            out["timestamp"] = np.arange(len(df), dtype=float)

        out["flow_duration_sec"] = df[col_map.get("flow duration", col_map.get("flow_duration", ""))] / 1e6 if "flow duration" in col_map else 1.0
        out["fwd_packets_total"] = df.get(col_map.get("tot fwd pkts", col_map.get("total fwd packets", "")), 1)
        out["bwd_packets_total"] = df.get(col_map.get("tot bwd pkts", col_map.get("total backward packets", "")), 1)
        out["fwd_bytes_total"] = df.get(col_map.get("totlen fwd pkts", col_map.get("total length of fwd packets", "")), 64)
        out["bwd_bytes_total"] = df.get(col_map.get("totlen bwd pkts", col_map.get("total length of bwd packets", "")), 64)
        out["syn_flag_count"] = df.get(col_map.get("syn flag cnt", col_map.get("syn flag count", "")), 0)
        out["rst_flag_count"] = df.get(col_map.get("rst flag cnt", col_map.get("rst flag count", "")), 0)
        out["fin_flag_count"] = df.get(col_map.get("fin flag cnt", col_map.get("fin flag count", "")), 0)
        out["psh_flag_count"] = df.get(col_map.get("psh flag cnt", col_map.get("psh flag count", "")), 0)
        out["dst_port"] = df.get(col_map.get("dst port", col_map.get("destination port", "")), 80)
        out["src_port"] = df.get(col_map.get("src port", col_map.get("source port", "")), 1024)

        # Label mapping
        label_col = col_map.get("label", None)
        if label_col:
            out["stage"] = df[label_col].astype(str).str.lower().str.strip().map(lambda x: CIC_IDS_2018_LABEL_MAP.get(x, "Execution" if "ddos" in x or "dos" in x else "Normal"))
        else:
            out["stage"] = "Normal"

        out["is_synthetic"] = False
        return out

    @staticmethod
    def _adapt_unsw_nb15(df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        col_map = {c.lower(): c for c in df.columns}
        
        out["timestamp"] = np.arange(len(df), dtype=float)
        out["flow_duration_sec"] = df.get(col_map.get("dur", ""), 1.0)
        out["fwd_packets_total"] = df.get(col_map.get("spkts", ""), 1)
        out["bwd_packets_total"] = df.get(col_map.get("dpkts", ""), 1)
        out["fwd_bytes_total"] = df.get(col_map.get("sbytes", ""), 64)
        out["bwd_bytes_total"] = df.get(col_map.get("dbytes", ""), 64)
        out["syn_flag_count"] = df.get(col_map.get("synack", ""), 0)
        out["dst_port"] = df.get(col_map.get("dsport", ""), 80)
        out["src_port"] = df.get(col_map.get("sport", ""), 1024)
        
        cat_col = col_map.get("attack_cat", col_map.get("label", None))
        if cat_col:
            out["stage"] = df[cat_col].astype(str).str.lower().str.strip().map(lambda x: UNSW_NB15_LABEL_MAP.get(x, "Normal" if x in ["0", "normal"] else "Execution"))
        else:
            out["stage"] = "Normal"
            
        out["is_synthetic"] = False
        return out

    @staticmethod
    def _adapt_ctu13(df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        col_map = {c.lower(): c for c in df.columns}
        
        out["timestamp"] = np.arange(len(df), dtype=float)
        out["flow_duration_sec"] = df.get(col_map.get("dur", ""), 1.0)
        out["fwd_packets_total"] = df.get(col_map.get("totpkts", ""), 1)
        out["bwd_packets_total"] = 0
        out["fwd_bytes_total"] = df.get(col_map.get("totbytes", col_map.get("srcbytes", "")), 64)
        out["bwd_bytes_total"] = 0
        out["dst_port"] = df.get(col_map.get("dport", ""), 80)
        out["src_port"] = df.get(col_map.get("sport", ""), 1024)
        
        label_col = col_map.get("label", None)
        if label_col:
            out["stage"] = df[label_col].astype(str).str.lower().str.strip().map(lambda x: "Command and Control" if "botnet" in x or "c&c" in x else ("Reconnaissance" if "scan" in x else "Normal"))
        else:
            out["stage"] = "Normal"
            
        out["is_synthetic"] = False
        return out

    @staticmethod
    def _adapt_generic(df: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame()
        col_map = {c.lower(): c for c in df.columns}
        
        out["timestamp"] = df[col_map["timestamp"]] if "timestamp" in col_map else np.arange(len(df), dtype=float)
        out["flow_duration_sec"] = df.get(col_map.get("flow_duration_sec", col_map.get("duration", "")), 1.0)
        out["fwd_packets_total"] = df.get(col_map.get("fwd_packets_total", col_map.get("packets", "")), 1)
        out["bwd_packets_total"] = df.get(col_map.get("bwd_packets_total", ""), 1)
        out["fwd_bytes_total"] = df.get(col_map.get("fwd_bytes_total", col_map.get("bytes", "")), 64)
        out["bwd_bytes_total"] = df.get(col_map.get("bwd_bytes_total", ""), 64)
        
        out["stage"] = df.get(col_map.get("stage", col_map.get("label", "")), "Normal")
        out["is_synthetic"] = False
        return out

    @classmethod
    def parse_pcap(cls, pcap_path: Path) -> pd.DataFrame:
        """Parses raw PCAP file using Scapy and extracts basic flow metadata."""
        try:
            from scapy.all import rdpcap, IP, TCP, UDP
            packets = rdpcap(str(pcap_path))
            records = []
            start_time = float(packets[0].time) if len(packets) > 0 else 0.0
            
            for pkt in packets:
                if IP in pkt:
                    rec = {
                        "timestamp": float(pkt.time) - start_time,
                        "src_ip": pkt[IP].src,
                        "dst_ip": pkt[IP].dst,
                        "proto": pkt[IP].proto,
                        "fwd_bytes_total": len(pkt),
                        "bwd_bytes_total": 0,
                        "fwd_packets_total": 1,
                        "bwd_packets_total": 0,
                        "syn_flag_count": 1 if TCP in pkt and pkt[TCP].flags.S else 0,
                        "rst_flag_count": 1 if TCP in pkt and pkt[TCP].flags.R else 0,
                        "fin_flag_count": 1 if TCP in pkt and pkt[TCP].flags.F else 0,
                        "psh_flag_count": 1 if TCP in pkt and pkt[TCP].flags.P else 0,
                        "src_port": pkt[TCP].sport if TCP in pkt else (pkt[UDP].sport if UDP in pkt else 0),
                        "dst_port": pkt[TCP].dport if TCP in pkt else (pkt[UDP].dport if UDP in pkt else 0),
                        "stage": "Normal",
                        "is_synthetic": False
                    }
                    records.append(rec)
            return pd.DataFrame(records)
        except Exception as e:
            # Return empty if parsing failed
            return pd.DataFrame()
