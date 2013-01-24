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
package com.mti.primitives;
import java.util.Vector;
/**
 *
 * @author nathan
 */
public abstract class Primitives {
    
    final static String Version = "1.0.0";
    /**
     * The LibraryPath global variable should define the file folder location
     * for the JNI enabled dynamic library that implements the functions needed
     * for this class library. This value must be set before any class within this
     * namespace can be declared or instantiated.
     */
    public static String LibraryPath = "";
    /**
     * The DependencyPaths list should define any dependencies that are used
     * by this library and/or it's JNI library. The values provided to this vector
     * can either be a file path or a HTTP URL. When the "InitializePrimitives"
     * function is called, the function will download or copy all dependencies
     * defined in this list to the path specified by "LibraryPath". If all 
     * dependencies are already present in the LibraryPath file location, then there
     * is no need to add any values to this vector. All libraries, whether a dependency
     * or the actual JNI library needed, should be included in this list, should they
     * need to be downloaded.
     */
    public static Vector<String> DependencyPaths = new Vector();
    
    /**
     * The NativeLibraries vector list should contain all of the JNI libraries that
     * implement the native functionality of the classes defined in this namespace.
     */
    public static Vector<String> NativeLibraries = new Vector();
    /**
     * The InitializePrimitives function is used to load all JNI libraries needed
     * to provide the native functionality for the classes within this library.
     * @return Returns true if the function successfully loaded all libraries,
     * false if there was a problem doing so.
     */
    public static boolean InitializePrimitives(){
        boolean retval = true;
        try{
            String separator = System.getProperty("file.separator");
            String binpath = System.getProperty("java.home");
            String archtype = System.getProperty("os.arch");
            String osname = System.getProperty("os.name");
            String osversion = System.getProperty("os.version");
            
            System.out.println("***********************************************");
            System.out.println("** ObjectiveMedia Java Implementation");
            System.out.println("** Version " + Version);
            System.out.println("***********************************************");
            System.out.println("\tPath Separator = " + separator);
            System.out.println("\tJava Binary Location = " + binpath);
            System.out.println("\tSystem Architecture = " + archtype);
            System.out.println("\tOperating System = " + osname);
            System.out.println("\tOS version = " + osversion);
            
            System.out.println("Initializing com.mti.primitives JNI libraries...");
            System.out.println("\tCopying dependencies to Library Path...");
            //TODO: Add function to copy files to Library Path.
            System.out.println("\tLoading JNI Libraries");
            if(!LibraryPath.endsWith(separator))
                LibraryPath = LibraryPath + separator;
            for(int x = 0; x < NativeLibraries.size(); x++){
                String path = LibraryPath + NativeLibraries.get(x);
                System.out.println("\t\t Loading " + path);
                System.load(path);
            }
        }catch(Exception e){
            System.out.println(e.getMessage());
            System.out.println(e.getStackTrace().toString());
            retval = false;
        }
        return retval;
    }
}
