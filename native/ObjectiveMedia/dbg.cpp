/*
 * copyright (c) 2013 Nathan Skipper, Montgomery Technology, Inc.
 *
 * This file is part of ObjectiveMedia (http://nskipper1110.github.com/objectivemedia).
 *
 * ObjectiveMedia is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * ObjectiveMedia is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with ObjectiveMedia; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
#include "dbg.h"

void WriteErrorMsg(char* file, char* text)
{
#ifdef _DEBUG
	FILE* fout;
	fout = fopen(file, "a");
	fprintf(fout, text);
	fclose(fout);
#endif
        printf("%s", text);
}

void DbgOut(char* msg){
	WriteErrorMsg("c:\\users\\nathan\\Desktop\\com_objectivemedia_dbg.txt", msg);
        //printf(msg);
}