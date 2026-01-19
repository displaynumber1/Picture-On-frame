/**
 * LAYER 3 - Auto Mode Decision Engine
 * Pure function to resolve photography mode from normalized input
 */

import { NormalizedGenerationInput } from './normalization';

export type PhotographyMode = 'catalog' | 'lifestyle';

/**
 * Categories that logically imply lifestyle usage
 */
const LIFESTYLE_CATEGORIES = [
  'Home Living',
  'Food & Beverage',
  'Tas', // Bags - often used in lifestyle contexts
];

/**
 * Styles that logically imply lifestyle usage
 */
const LIFESTYLE_STYLES = [
  'Lifestyle',
  'Indoor/Outdoor',
  'Outdoor Cafe',
];

/**
 * Resolve photography mode
 * 
 * If mode === 'auto':
 *   - Choose 'lifestyle' ONLY if:
 *       - backgroundImage exists AND
 *       - style or category logically implies lifestyle usage
 *   - Otherwise fallback to 'catalog'
 * 
 * @param normalizedInput - Normalized generation input
 * @param rawMode - Original mode from user input
 * @returns Resolved photography mode
 */
export function resolvePhotographyMode(
  normalizedInput: NormalizedGenerationInput,
  rawMode: 'auto' | 'catalog' | 'lifestyle'
): PhotographyMode {
  // If mode is explicitly set, use it
  if (rawMode !== 'auto') {
    return rawMode;
  }
  
  // AUTO MODE: Rule-based decision
  // Lifestyle requires BOTH conditions:
  // 1. Background image exists
  // 2. Style or category implies lifestyle
  
  const hasBackground = normalizedInput.hasBackground;
  const styleImpliesLifestyle = normalizedInput.style 
    ? LIFESTYLE_STYLES.includes(normalizedInput.style)
    : false;
  const categoryImpliesLifestyle = normalizedInput.category
    ? LIFESTYLE_CATEGORIES.includes(normalizedInput.category)
    : false;
  
  const logicalImpliesLifestyle = styleImpliesLifestyle || categoryImpliesLifestyle;
  
  if (hasBackground && logicalImpliesLifestyle) {
    return 'lifestyle';
  }
  
  // Default fallback to catalog
  return 'catalog';
}
