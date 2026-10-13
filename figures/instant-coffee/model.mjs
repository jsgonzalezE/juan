// The truth the figure is built from. Every number the card shows comes from here.
// One batch of green coffee goes through roasting, grinding, extraction, concentration,
// freezing, granulating, freeze drying and packing. Typical industrial values:
// roasting loses 15–18 % of the green weight; soluble yield 35–50 % of the roast and ground
// mass; extract 15–25 % solids; concentrate 40–50 % solids; the concentrate is frozen on a
// belt at about −45 °C, broken into 1–3 mm granules, and dried under about 0.5 mbar where the
// ice sublimates; granules leave at 2–4 % moisture; about 2 g per cup.

export const BATCH = { green: 120, roastLoss: 0.167, yield: 0.4, extractSolids: 0.2, concSolids: 0.45, powderSolids: 0.97, cupDose: 2 };
export const PLANT = { roastC: 215, roastMinutes: 12, grindMm: 1, waterC: 170, kettleC: 50, vacuumBar: 0.9, beltC: -45, granuleMm: "1–3", dryMbar: 0.5, shelfC: 50, dryHours: 7 };
export const STAGES = ["ready", "roasting", "grinding", "extracting", "concentrating", "freezing", "granulating", "freeze drying", "packing", "done"];
export const LAST = STAGES.length - 1; // s runs 0..LAST; stage k covers s in [k-1, k)

export function balance(b = BATCH) {
  const ground = b.green * (1 - b.roastLoss);
  const solids = ground * b.yield;
  const extract = solids / b.extractSolids;
  const concentrate = solids / b.concSolids;
  const powder = solids / b.powderSolids;
  return {
    green: b.green,
    roastLoss: b.green - ground,
    ground,
    solids,
    spent: ground - solids,
    extract,
    waterIn: extract - solids,
    concentrate,
    evaporated: extract - concentrate,
    ice: concentrate - powder,
    powder,
    cups: powder / b.cupDose,
  };
}

export const clamp01 = (v) => Math.min(1, Math.max(0, v));
export const ease = (x) => {
  const t = clamp01(x);
  return t * t * (3 - 2 * t);
};
// A window inside a stage: 0 before `from`, 1 between, 0 after `to`, with soft edges.
const win = (f, from, to, edge = 0.08) => ease((f - from) / edge) * (1 - ease((f - to) / edge));

export function stateAt(s, b = BATCH) {
  s = Math.max(0, Math.min(LAST, s));
  const B = balance(b);
  const stage = s >= LAST - 1e-9 ? LAST : s <= 1e-9 ? 0 : Math.floor(s + 1e-9) + 1;
  const f = stage === LAST ? 1 : stage === 0 ? 0 : s - (stage - 1);
  const done = (k) => (stage > k ? 1 : stage === k ? f : 0); // progress of stage k, 0..1
  const g = (v) => Math.round(v);
  const pct = (v) => `${Math.round(v * 100)} %`;

  // 1 roasting: beans leave the silo, tumble in the drum, cool on the tray
  const roast = done(1);
  const beansIn = stage === 1 ? win(f, 0, 0.45) : 0;
  const drumTurning = stage === 1 ? win(f, 0.05, 0.95, 0.1) : 0;
  const roastC = 20 + (PLANT.roastC - 20) * (stage === 1 ? ease(f / 0.3) * (1 - ease((f - 0.8) / 0.2)) : 0);
  const beansOut = stage === 1 ? win(f, 0.5, 0.95) : 0;
  const roasted = B.green - B.roastLoss * ease(roast);
  // 2 grinding: beans climb to the mill, grounds climb to the column
  const grindIn = stage === 2 ? win(f, 0, 0.55) : 0;
  const rollersTurning = stage === 2 ? win(f, 0.05, 0.9, 0.1) : 0;
  const groundsOut = stage === 2 ? win(f, 0.25, 0.95) : 0;
  const bed = stage < 2 ? 0 : stage === 2 ? ease((f - 0.35) / 0.55) : 1;
  const groundMass = B.ground * done(2);
  // 3 extraction (water in, sump below the plate, extract to the kettle)
  const ex = done(3);
  const extractOut = B.extract * ex;
  const water = stage === 3 ? ease(f / 0.3) * (1 - ease((f - 0.82) / 0.18)) : 0;
  const sump = stage === 3 ? ease((f - 0.08) / 0.3) * (1 - ease((f - 0.9) / 0.1)) : 0;
  const heat = stage === 3 ? ease(f / 0.25) : stage === 4 ? 1 - ease(f / 0.3) : 0;
  const waterC = 20 + (PLANT.waterC - 20) * heat;
  // 4 concentration
  let kettle = 0;
  if (stage === 3) kettle = extractOut;
  else if (stage === 4) kettle = B.extract - B.evaporated * f;
  else if (stage === 5) kettle = B.concentrate * (1 - f);
  const kettleSolids = stage <= 3 ? b.extractSolids : stage === 4 ? B.solids / Math.max(kettle, 1e-6) : b.concSolids;
  const evaporated = stage < 4 ? 0 : stage === 4 ? B.evaporated * f : B.evaporated;
  const boiling = stage === 4 ? win(f, 0, 0.9, 0.12) : 0;
  const vacuum = stage === 4 ? ease(f / 0.15) : stage === 5 ? 1 - ease(f / 0.12) : 0;
  // 5 freezing: the concentrate is poured on the belt and leaves the tunnel as a frozen slab
  const pouring = stage === 5 ? win(f, 0, 0.85) : 0;
  const slab = stage < 5 ? 0 : stage === 5 ? ease((f - 0.05) / 0.9) : 1; // how far along the belt the slab reaches
  const beltRun = stage === 5 ? win(f, 0, 0.95) : stage === 6 ? win(f, 0, 0.9) : 0; // the belt moves while the slab forms and while it is fed off
  const beltC = 20 + (PLANT.beltC - 20) * (stage === 5 ? ease(f / 0.2) : stage === 6 ? 1 - ease(f / 0.3) : 0);
  // 6 granulating: the slab goes into the mill, granules travel to the dryer trays
  const slabIn = stage < 6 ? 0 : stage === 6 ? ease(f / 0.9) : 1; // share of the slab eaten by the mill
  const rotorTurning = stage === 6 ? win(f, 0.03, 0.95, 0.1) : 0;
  const granulesOut = stage === 6 ? win(f, 0.12, 0.95) : 0;
  const trays = stage < 6 ? 0 : stage === 6 ? ease((f - 0.2) / 0.7) : 1; // how full the dryer trays are
  // 7 freeze drying: vacuum, warm shelves, ice sublimates to the condenser
  const dryVac = stage === 7 ? ease(f / 0.15) : stage === 8 ? 1 - ease(f / 0.12) : 0;
  const subliming = stage === 7 ? win(f, 0.1, 0.9, 0.12) : 0;
  const dried = stage < 7 ? 0 : stage === 7 ? ease((f - 0.12) / 0.8) : 1;
  const iceGone = B.ice * dried;
  const shelfC = 20 + (PLANT.shelfC - 20) * (stage === 7 ? ease(f / 0.25) : 0);
  // 8 packing: granules climb to the filler, the jar fills, the cap goes on
  const packIn = stage === 8 ? win(f, 0, 0.6) : 0;
  const jar = stage < 8 ? 0 : stage === 8 ? ease((f - 0.15) / 0.6) : 1;
  const capped = stage < 8 ? 0 : stage === 8 ? ease((f - 0.82) / 0.15) : 1;
  const powder = B.powder * done(8);
  // gauge needles, 0..1
  const roastShare = (roastC - 20) / (PLANT.roastC - 20);
  const beltShare = (20 - beltC) / (20 - PLANT.beltC);

  let readout;
  if (stage === 0) readout = `ready · ${g(b.green)} g of green coffee`;
  else if (stage === 1) readout = `roasting · ${g(roastC)} °C · ${g(roasted)} g`;
  else if (stage === 2) readout = `grinding · ${g(groundMass)} g · ${PLANT.grindMm} mm grind`;
  else if (stage === 3) readout = `extracting · ${g(extractOut)} g of extract · ${g(waterC)} °C`;
  else if (stage === 4) readout = `boiling off · ${g(evaporated)} g of water · ${pct(kettleSolids)} solids`;
  else if (stage === 5) readout = `freezing · ${g(beltC)} °C belt · ${g(B.concentrate * slab)} g frozen`;
  else if (stage === 6) readout = `granulating · ${g(B.concentrate * slabIn)} g · ${PLANT.granuleMm} mm`;
  else if (stage === 7) readout = `freeze drying · ${PLANT.dryMbar} mbar · ${g(iceGone)} g of ice gone`;
  else if (stage === 8) readout = `packing · ${g(powder)} g in the jar`;
  else readout = `done · ${g(B.powder)} g of instant · about ${g(B.cups)} cups`;

  return {
    stage, f, B, readout, phase: STAGES[stage],
    roast, beansIn, drumTurning, roastC, beansOut, roasted,
    grindIn, rollersTurning, groundsOut, bed, groundMass,
    extractOut, water, sump, waterC,
    kettle, kettleFill: kettle / B.extract, kettleSolids, evaporated, condensate: evaporated / B.evaporated, boiling, vacuum,
    pouring, slab, beltRun, beltC,
    slabIn, rotorTurning, granulesOut, trays,
    dryVac, subliming, dried, iceGone, shelfC,
    packIn, jar, capped, powder, roastShare, beltShare, heat,
  };
}
