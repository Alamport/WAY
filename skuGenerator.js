/*
File: skuGenerator.gs
Author: Masato Nobunaga
Date: 06-04-2025
Description: Generates a unique SKU for items in a google sheet
Flow: Duplicate receipt template -> extract info from product order -> write details into order receipt -> print order receipt as a pdf
*/

var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
var generatedSKUs = new Set();

/* =========================== Duplicate Product List =========================== */
function duplicate() {
  spreadsheet.setActiveSheet(spreadsheet.getSheetByName('Main'));
  let prodListDupe = SpreadsheetApp.getActiveSpreadsheet().duplicateActiveSheet();

  return prodListDupe;
}

function findVals(row) {
  const sku = {
    vendor: "",
    productType: "",
    color: ""
  };

  let vendorCol = 3;
  let productTypeCol = 5;
  let colorCol = 9;

  sku.vendor = row[vendorCol];
  sku.productType = row[productTypeCol];
  sku.color = row[colorCol];
  // Logger.log(sku);
  return sku;
}
/* =========================== SKU Generator =========================== */

// returns the first 3 letters back (000 represents in the case it's empty)
function toLetterCode(str = "000", numDigits) {
  return str.replace(/[^a-zA-Z]/g, '').substring(0, numDigits).toUpperCase();
}

// finds a random id number between 1000 and 9999 (it is considered bad practice to start with 0)
function getRandomId() {
  return Math.floor(1000 + Math.random() * 9000)
}

function generateSKU({vendor, productType, color}) {
  const vendorCode = companyAcronyms[vendor] || toLetterCode(vendor, 3);
  const typeCode = productTypeAcronyms[productType] || toLetterCode(productType, 3);
  // const typeCode = to3LetterCode(productType);
  // const styleCode = to3LetterCode(style || "GEN");
  const colorCode = toLetterCode(color || "CLR", 3);

  let sku;
  let attempts = 0;

  do {
    const id = getRandomId();
    sku =  `${vendorCode}-${typeCode}-${colorCode}-${id}`;
    attempts++;
    if (attempts > 1001) {
      throw new Error("Too many SKU collisions, consider a bigger ID space!");
    }
  } while (generatedSKUs.has(sku));

  generatedSKUs.add(sku);
  return sku;
}

/* =========================== Duplicate Product List =========================== */
// goes through a spreadsheet and generates SKUs
function iterator(prodListDupe) {
  let allRows = prodListDupe.getDataRange().getValues();
  let skuValues = [];
  let lastKnownVendor = "";
  let lastKnownProductType = "";
  let lastProductId = "";

  for (let i = 1; i < allRows.length; i++) {
    let row = allRows[i];
    let productId = row[0];          // Column A
    let vendor = row[3];             // Column D
    let productType = row[5];        // Column F
    let color = row[9];              // Column J
    let sku = row[17];               // Column R

    if (vendor) lastKnownVendor = vendor;

    // Handling product type:
    if (productType) {
      lastKnownProductType = productType;
    } else if (productId !== lastProductId) {
      // This is not a color variant, reset productType to "000"
      lastKnownProductType = "000";
    }

    lastProductId = productId; // Track for next row

    if (color) {
      if (!sku) {
        let skuInfo = {
          vendor: lastKnownVendor,
          productType: lastKnownProductType,
          color: color
        };
        let generated = generateSKU(skuInfo);
        row[17] = generated;
        Logger.log(`Generated SKU: ${generated}`);
      } else {
        generatedSKUs.add(sku);
      }
    }
  }

  // Write all updated rows back to the sheet (just column R)
  let output = allRows.slice(1).map(r => [r[17]]); // from row 2 onward
  prodListDupe.getRange(2, 18, output.length, 1).setValues(output);
}


function main() {
  let prodListDupe = duplicate();
  iterator(prodListDupe);

  Logger.log(generatedSKUs.size);

  // Logger.log(generatedSKUs);
  Logger.log("COMPLETED");
}
 
main();
