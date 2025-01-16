//===--- UseCaptureByCheck.cpp - clang-tidy -------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "UseCaptureByCheck.h"
#include "clang/ASTMatchers/ASTMatchFinder.h"

using namespace clang::ast_matchers;

namespace clang::tidy::lifetime {

void UseCaptureByCheck::registerMatchers(MatchFinder *Finder) {}

void UseCaptureByCheck::check(const MatchFinder::MatchResult &Result) {}

} // namespace clang::tidy::lifetime
