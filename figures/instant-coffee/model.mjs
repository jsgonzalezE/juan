// The truth the figure is built from. Every number the card shows comes from here.
// One batch of roast and ground coffee goes through extraction, concentration and spray drying.
// Typical industrial values: soluble yield 35–50 % of the roast and ground mass, extract 15–25 % solids,
// concentrate 40–50 % solids before drying, powder at 2–4 % moisture, about 2 g per cup.

export const BATCH = { ground: 100, yield: 0.4, extractSolids: 0.2, concSolids: 0.45, powderSolids: 0.97, cupDose: 2 };
export const PLANT = { waterC: 170, kettleC: 50, vacuumBar: 0.9, airInC: 250, airOutC: 105 };
export const STAGES = ["ready", "extracting", "concentrating", "spray drying", "done"];

export function balance(b = BATCH) {
  const solids = b.ground * b.yield;
  const extract = solids / b.extractSolids;
  const concentrate = solids / b.concSolids;
  const powder = solids / b.powderSolids;
  return {
    solids,
    spent: b.ground - solids,
    extract,
    waterIn: extract - solids,
    concentrate,
    evaporated: extract - concentrate,
    powder,
    dried: concentrate - powder,
    cups: powder / b.cupDose,
  };
}

export const clamp01 = (v) => Math.min(1, Math.max(0, v));
export const ease = (x) => {
  const t = clamp01(x);
  return t * t * (3 - 2 * t);
};

// s runs 0..3: 0 ready, 0..1 extraction, 1..2 concentration, 2..3 spray drying, 3 done.
export function stateAt(s, b = BATCH) {
  s = Math.max(0, Math.min(3, s));
  const B = balance(b);
  const stage = s >= 3 - 1e-9 ? 4 : s <= 1e-9 ? 0 : Math.floor(s + 1e-9) + 1;
  const f = stage === 4 ? 1 : stage === 0 ? 0 : s - (stage - 1);
  const ex = stage < 1 ? 0 : stage === 1 ? f : 1;
  const extractOut = B.extract * ex;
  const water = stage === 1 ? ease(f / 0.3) * (1 - ease((f - 0.82) / 0.18)) : 0;
  const sump = stage === 1 ? ease((f - 0.08) / 0.3) * (1 - ease((f - 0.9) / 0.1)) : 0;
  let kettle = 0;
  if (stage === 1) kettle = extractOut;
  else if (stage === 2) kettle = B.extract - B.evaporated * f;
  else if (stage === 3) kettle = B.concentrate * (1 - f);
  const kettleSolids = stage <= 1 ? b.extractSolids : stage === 2 ? B.solids / Math.max(kettle, 1e-6) : b.concSolids;
  const evaporated = stage < 2 ? 0 : stage === 2 ? B.evaporated * f : B.evaporated;
  const boiling = stage === 2 ? ease(f / 0.12) * (1 - ease((f - 0.9) / 0.1)) : 0;
  const vacuum = stage === 2 ? ease(f / 0.15) : stage === 3 ? 1 - ease(f / 0.12) : 0;
  const dried = stage < 3 ? 0 : stage === 3 ? f : 1;
  const powder = B.powder * dried;
  const spraying = stage === 3 ? ease(f / 0.08) * (1 - ease((f - 0.94) / 0.06)) : 0;
  const airHot = stage === 3 ? ease(f / 0.1) : stage === 4 ? 0 : 0;
  const heat = stage === 1 ? ease(f / 0.25) : stage === 2 ? 1 - ease(f / 0.3) : 0;
  const waterC = 20 + (PLANT.waterC - 20) * heat;
  const airIn = 20 + (PLANT.airInC - 20) * airHot;
  const g = (v) => Math.round(v);
  const pct = (v) => `${Math.round(v * 100)} %`;
  let readout;
  if (stage === 0) readout = `ready · ${g(b.ground)} g of ground coffee`;
  else if (stage === 1) readout = `extracting · ${g(extractOut)} g of extract · ${g(waterC)} °C`;
  else if (stage === 2) readout = `boiling off · ${g(evaporated)} g of water · ${pct(kettleSolids)} solids`;
  else if (stage === 3) readout = `spray drying · ${g(powder)} g of powder · ${g(airIn)} °C air`;
  else readout = `done · ${g(B.powder)} g of instant · about ${g(B.cups)} cups`;
  return {
    stage,
    f,
    B,
    extractOut,
    water,
    sump,
    kettle,
    kettleFill: kettle / B.extract,
    kettleSolids,
    evaporated,
    condensate: evaporated / B.evaporated,
    boiling,
    vacuum,
    dried,
    powder,
    spraying,
    airHot,
    waterC,
    airIn,
    readout,
    phase: STAGES[stage],
  };
}
