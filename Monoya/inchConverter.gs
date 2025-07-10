/**
 * File: inchConverter.gs
 * Author: Masato Nobunaga
 * Date: 06-07-2025
 * Description: Syncs inch notation for a given column
 * Flow: Duplicate product info -> Access the product dimension column -> go through every cell with dimensions and correct inch notations to ASCII
 */

/* =========================== Dimension Normalizing Functions =========================== */

/** 
 * Converts all variations of inch dimensions to one standard
 * */ 
function normalizeDimensions(text) {
  text = preprocessText(text);

  const segments = text.split('x');

  const cleanedSegments = segments.map((segment) => {
    segment = segment.trim();

    // Skip if already quoted
    if (segment.endsWith('"')) return segment;

    // Handle dimension ranges like "1.0–2.0" or "1.0 to 2.0"
    const rangeSeparators = /(-|–|—| to )/;
    if (rangeSeparators.test(segment)) {
      const parts = segment.split(rangeSeparators);
      return parts
        .map((part, i) => {
          part = part.trim();
          // Only quote numeric parts (not the separator)
          const isNumeric = /^φ?-?\d+(\.\d+)?$/.test(part);
          return isNumeric ? part + '"' : part;
        })
        .join('');
    }

    // Regular single-number match at the end
    const match = segment.match(/(φ?-?\d+(\.\d+)?)$/);
    if (match) {
      const number = match[1];
      return segment.replace(/(φ?-?\d+(\.\d+)?)$/, number + '"');
    } else {
      return segment;
    }
  });

  return cleanedSegments.join('x');
}

/** 
 * Ensures that all given text are in proper ASCII form and proper formatting is done 
 * */ 
function preprocessText(text) {
  if (typeof text !== 'string') return '';

  return text
    // 1. Normalize whitespace around × or x to just 'x'
    .replace(/\s*[×x]\s*/g, 'x')

    // 2. Remove trailing punctuation after numbers (except quotes)
    .replace(/(\d+(\.\d+)?)[.,;]+(?=\s|$)/g, '$1')

    // 3. Convert full-width digits and full-width dot to ASCII
    .replace(/[０-９．]/g, (char) => {
      if (char >= '０' && char <= '９') {
        return String.fromCharCode(char.charCodeAt(0) - 65248);
      }
      if (char === '．') return '.';
      return char;
    })

    // 4. Normalize Unicode minus sign to ASCII dash
    .replace(/\u2212/g, '-');
}

/* =========================== Helper Function =========================== */

/** 
 * Creates a duplicate of the original csv to ensure safekeeping
 * */ 
function duplicate() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  spreadsheet.setActiveSheet(spreadsheet.getSheetByName('Main'));
  let prodListDupe = SpreadsheetApp.getActiveSpreadsheet().duplicateActiveSheet();

  return prodListDupe;
}


/* =========================== Driver Function =========================== */

/** 
 * Driver function that connects all the functions together
 * */ 
function main() {
  let prodListDupe = duplicate();
  let lastRow = prodListDupe.getLastRow();
  let productDimCol = 59
  let curCellRow = 2;
  let productDimColVals = prodListDupe.getSheetValues(curCellRow, productDimCol, lastRow + 1, 1); // row | col | numOfRows | numOfCols. ** col BG = 59 **

  // iterates through all product dimensions, correcting each one along the way
  productDimColVals.forEach((dims) => {
    const dimValue = dims[0];

    if (typeof dimValue === 'string' && dimValue.trim() !== '') {
      const result = normalizeDimensions(dimValue);
      // sets the new, converted value in its original cell 
      prodListDupe.getRange(curCellRow, productDimCol).setValue(result);
      console.log(`Before: ${dimValue}\nAfter : ${result}\n`);
    } else {
      // console.log(`Skipping invalid or empty value: ${dimValue}`);
    }
    curCellRow += 1;
  });
}

main();
