/**
 * Real output of models/train.py, from data/anomaly_scores.csv in the first commit
 * of AI-Powered-Insider-Threat-Detection-Defense-System (commit 87e568e).
 * Twenty simulated users, three of them planted by the red-team simulator.
 * Higher means more anomalous. Values rounded to five decimals.
 */
export type Detector = "isolationForest" | "oneClassSvm" | "autoencoder";

export type ScoredUser = {
  user: string;
  planted: boolean;
  isolationForest: number;
  oneClassSvm: number;
  autoencoder: number;
};

export const DETECTORS: { id: Detector; label: string }[] = [
  { id: "isolationForest", label: "Isolation forest" },
  { id: "oneClassSvm", label: "One-class SVM" },
  { id: "autoencoder", label: "Autoencoder" },
];

export const SCORES: ScoredUser[] = [
  { user: "user1", planted: false, isolationForest: 0.43414, oneClassSvm: -0.10194, autoencoder: 0.13166 },
  { user: "user2", planted: false, isolationForest: 0.45461, oneClassSvm: -0.02427, autoencoder: 0.303 },
  { user: "user3", planted: false, isolationForest: 0.48683, oneClassSvm: -0.00039, autoencoder: 0.0922 },
  { user: "user4", planted: false, isolationForest: 0.47319, oneClassSvm: 0.00028, autoencoder: 0.46299 },
  { user: "user5", planted: false, isolationForest: 0.52456, oneClassSvm: -0.00002, autoencoder: 0.36277 },
  { user: "user6", planted: false, isolationForest: 0.49864, oneClassSvm: -0.00009, autoencoder: 0.82589 },
  { user: "user7", planted: true, isolationForest: 0.47511, oneClassSvm: -0.00005, autoencoder: 0.14652 },
  { user: "user8", planted: false, isolationForest: 0.49836, oneClassSvm: -0.00048, autoencoder: 0.10814 },
  { user: "user9", planted: false, isolationForest: 0.48405, oneClassSvm: 0.00038, autoencoder: 0.55939 },
  { user: "user10", planted: false, isolationForest: 0.46489, oneClassSvm: -0.00008, autoencoder: 0.57616 },
  { user: "user11", planted: false, isolationForest: 0.40653, oneClassSvm: -0.1307, autoencoder: 0.1413 },
  { user: "user12", planted: false, isolationForest: 0.52866, oneClassSvm: 0.00017, autoencoder: 0.41001 },
  { user: "user13", planted: true, isolationForest: 0.55546, oneClassSvm: -0.0001, autoencoder: 1.39365 },
  { user: "user14", planted: false, isolationForest: 0.43514, oneClassSvm: -0.05156, autoencoder: 0.25625 },
  { user: "user15", planted: false, isolationForest: 0.49803, oneClassSvm: -0.00023, autoencoder: 0.8969 },
  { user: "user16", planted: false, isolationForest: 0.49438, oneClassSvm: 0.00011, autoencoder: 0.33914 },
  { user: "user17", planted: false, isolationForest: 0.46059, oneClassSvm: -0.00008, autoencoder: 0.03491 },
  { user: "user18", planted: false, isolationForest: 0.53028, oneClassSvm: 0.00018, autoencoder: 0.172 },
  { user: "user19", planted: false, isolationForest: 0.46322, oneClassSvm: -0.02509, autoencoder: 0.1631 },
  { user: "user20", planted: true, isolationForest: 0.55821, oneClassSvm: 0.0004, autoencoder: 0.03549 },
];
